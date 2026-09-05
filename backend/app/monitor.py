"""Monitoring service: connects capture → analysis → database → WebSocket.

This is the heart of the application. Flows closed by the tracker are
persisted to SQLite, privacy scores are recomputed, unencrypted
communication produces privacy alerts, and real-time updates are broadcast.

Real-time pipeline:
  - New flows emit a throttled `traffic_update` WebSocket event.
  - Every FLUSH_INTERVAL a full `live` snapshot is broadcast (batched).
  - Closed flows emit `connection_closed` (+ `alert` when created) followed by
    a fresh `live` snapshot.
Broadcasts are scheduled onto the running event loop from the capture thread
via manager.broadcast_sync.
"""
import logging
import socket
import time

from app.analysis.encryption_analyzer import encryption_label
from app.analysis.privacy_score import compute_privacy_score
from app.capture.packet_capture import PacketCaptureManager
from app.config import settings
from app.database import crud
from app.database.database import SessionLocal
from app.timeutils import to_iso_utc, to_naive_utc, utc_now_iso
from app.websocket.manager import manager

logger = logging.getLogger("privacy.monitor")


class PrivacyMonitor:
    def __init__(self):
        self.capture = None
        self._local_device = None
        self._last_flow_event = 0.0

    def _ensure_capture(self):
        if self.capture is None:
            self.capture = PacketCaptureManager(
                on_flow_close=self._on_flow_close,
                on_active_update=self._on_active_update,
            )
        return self.capture

    def _get_local_device(self):
        if self._local_device is not None:
            return self._local_device
        db = SessionLocal()
        try:
            device = crud.get_or_create_device(
                db,
                ip=hostname_ip(),
                hostname=socket.gethostname(),
                interface=(self.capture.interface or "Unknown") if self.capture else "Unknown",
            )
            device.name = "My Laptop"
            self._local_device = device.id
            db.commit()
            return self._local_device
        finally:
            db.close()

    def start(self):
        self._ensure_capture()
        if self.capture.is_running:
            return {"status": "running"}
        self.capture.start()
        self._broadcast({"type": "monitoring_status", "monitoring": self.status(),
                         "timestamp": utc_now_iso()})
        return {"status": "started", "mode": "demo" if self.capture.demo_mode else "live"}

    def stop(self):
        if self.capture is None:
            return {"status": "stopped"}
        self.capture.stop()
        self._broadcast({"type": "monitoring_status", "monitoring": self.status(),
                         "timestamp": utc_now_iso()})
        return {"status": "stopped"}

    def status(self) -> dict:
        self._ensure_capture()
        running = self.capture.is_running
        return {
            "running": running,
            "mode": "demo" if self.capture.demo_mode else "live",
            "interface": self.capture.interface or "auto",
            "demo_mode": self.capture.demo_mode,
            "last_error": self.capture._last_error,
        }

    def set_interface(self, interface: str) -> dict:
        self._ensure_capture()
        self.capture.set_interface(interface)
        return self.status()

    def set_demo_mode(self, enabled: bool) -> dict:
        self._ensure_capture()
        self.capture.set_demo_mode(enabled)
        return self.status()

    def _broadcast(self, message: dict):
        manager.broadcast_sync(message)

    def _on_flow_close(self, flow):
        alert_payload = None
        try:
            db = SessionLocal()
            try:
                alert_payload = self._persist_flow(db, flow)
            finally:
                db.close()
        except Exception as exc:
            logger.error("Failed to persist flow: %s", exc)
        self._broadcast(self._flow_event(flow, "connection_closed"))
        if alert_payload is not None:
            self._broadcast(alert_payload)
        self._broadcast(self.live_payload())

    def _persist_flow(self, db, flow):
        """Persist a closed flow; returns an alert event payload if one was
        created, otherwise None."""
        device_id = self._get_local_device()
        conn = crud.create_connection(
            db,
            device_id=device_id,
            timestamp=to_naive_utc(flow.first_seen),
            last_seen=to_naive_utc(flow.last_seen_dt),
            source_ip=flow.key.source_ip,
            destination_ip=flow.key.destination_ip,
            source_port=flow.key.source_port,
            destination_port=flow.key.destination_port,
            protocol=flow.key.protocol,
            service=flow.service,
            website=flow.website,
            domain=flow.domain,
            application=flow.application,
            encrypted=1 if flow.encrypted else 0,
            bytes_sent=flow.bytes_sent,
            bytes_received=flow.bytes_received,
            packets_sent=flow.packets_sent,
            packets_received=flow.packets_received,
            duration=flow.duration(),
            status="closed",
        )
        if not flow.encrypted:
            severity = "INFO" if flow.service == "DNS" else "WARNING"
            message = (
                f"Unencrypted communication detected — {flow.service or 'Unknown'} "
                f"({flow.key.protocol} port {flow.key.destination_port}) to "
                f"{flow.key.destination_ip}. Encryption: "
                f"{encryption_label(False, flow.key.protocol)}."
            )
            alert = crud.create_alert(
                db,
                message=message,
                severity=severity,
                connection_id=conn.id,
                device_id=device_id,
                alert_type="unencrypted",
            )
            logger.info("Privacy alert: unencrypted %s flow to %s:%s",
                        flow.service, flow.key.destination_ip, flow.key.destination_port)
            return {
                "type": "alert",
                "alert": {
                    "id": alert.id,
                    "timestamp": to_iso_utc(alert.timestamp),
                    "severity": alert.severity,
                    "message": alert.message,
                    "status": alert.status,
                },
            }
        return None

    def _on_active_update(self, flow, is_new, tick=False):
        if is_new and flow is not None:
            now = time.time()
            if now - self._last_flow_event >= settings.WS_MIN_INTERVAL_SECONDS:
                self._last_flow_event = now
                self._broadcast(self._flow_event(flow, "traffic_update"))
        if tick:
            self._broadcast(self.live_payload())

    def _flow_event(self, flow, event_type: str) -> dict:
        return {"type": event_type, "connection": self._flow_dict(flow)}

    def _flow_dict(self, flow) -> dict:
        return {
            "service": flow.service,
            "website": flow.website,
            "domain": flow.domain,
            "application": flow.application,
            "protocol": flow.key.protocol,
            "source_ip": flow.key.source_ip,
            "source_port": flow.key.source_port,
            "destination": flow.key.destination_ip,
            "destination_ip": flow.key.destination_ip,
            "destination_port": flow.key.destination_port,
            "port": flow.key.destination_port,
            "bytes_sent": flow.bytes_sent,
            "bytes_received": flow.bytes_received,
            "packets": flow.packets_sent + flow.packets_received,
            "encrypted": bool(flow.encrypted),
            "encryption": encryption_label(flow.encrypted, flow.key.protocol),
            "status": "closed" if flow.closed else "active",
            "timestamp": to_iso_utc(flow.first_seen),
            "started": to_iso_utc(flow.first_seen),
            "last_seen": to_iso_utc(flow.last_seen_dt),
            "duration": flow.duration(),
        }

    def _live_summary(self, db) -> dict:
        """DB summary merged with in-flight tracker flows so the dashboard
        reflects live traffic while capture is running (no double counting:
        active flows are not yet persisted)."""
        base = crud.get_connection_summary(db)
        active = self.capture.tracker.active_flows() if self.capture else []
        live_sent = sum(f.bytes_sent for f in active)
        live_received = sum(f.bytes_received for f in active)
        live_enc = sum(1 for f in active if f.encrypted)
        total = base["total_connections"] + len(active)
        encrypted = base["encrypted_connections"] + live_enc
        return {
            **base,
            "total_connections": total,
            "encrypted_connections": encrypted,
            "unencrypted_connections": total - encrypted,
            "bytes_sent": base["bytes_sent"] + live_sent,
            "bytes_received": base["bytes_received"] + live_received,
            "active_connections": len(active),
            "encrypted_percentage": round(encrypted / total * 100, 1) if total else 0.0,
        }

    def _top_websites(self, db, active_flows, limit: int = 10) -> list[dict]:
        agg: dict[str, dict] = {}
        for row in crud.get_websites(db, limit=1000):
            agg[row["website"]] = {"website": row["website"], "bytes": row["bytes"], "count": row["count"]}
        for f in active_flows:
            website = f.website or "Unknown"
            if website == "Unknown":
                continue
            item = agg.setdefault(website, {"website": website, "bytes": 0, "count": 0})
            item["bytes"] += f.bytes_sent + f.bytes_received
            item["count"] += 1
        ranked = sorted(agg.values(), key=lambda r: r["bytes"], reverse=True)
        return ranked[:limit]

    def live_payload(self) -> dict:
        db = SessionLocal()
        try:
            summary = self._live_summary(db)
            active_flows = self.capture.tracker.active_flows() if self.capture else []
            active_connections = [self._flow_dict(f) for f in active_flows]

            total = summary["total_connections"]
            encrypted = summary["encrypted_connections"]
            unencrypted_bytes = _unencrypted_bytes(db)
            score = compute_privacy_score(
                total_connections=total,
                encrypted_connections=encrypted,
                unencrypted_bytes=unencrypted_bytes,
                total_bytes=summary["bytes_sent"] + summary["bytes_received"],
            )

            recent = crud.get_recent_alerts(db, limit=10)
            return {
                "type": "live",
                "summary": summary,
                "privacy_score": score,
                "active_connections": active_connections,
                "alerts": [
                    {
                        "id": a.id,
                        "timestamp": to_iso_utc(a.timestamp),
                        "severity": a.severity,
                        "message": a.message,
                        "status": a.status,
                    }
                    for a in recent
                ],
                "websites": self._top_websites(db, active_flows, limit=10),
                "monitoring": self.status(),
                "demo_data": bool(self.capture.demo_mode) if self.capture else False,
                "timestamp": utc_now_iso(),
            }
        finally:
            db.close()


def hostname_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def _unencrypted_bytes(db) -> int:
    from sqlalchemy import func

    from app.database.models import Connection

    row = (
        db.query(func.coalesce(func.sum(Connection.bytes_sent + Connection.bytes_received), 0))
        .filter(Connection.encrypted == 0)
        .scalar()
    )
    return row or 0


monitor = PrivacyMonitor()