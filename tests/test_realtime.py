"""Real-time pipeline tests: live summary merging, flow events, broadcast."""
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.capture.packet_capture import FlowTracker, PacketCaptureManager  # noqa: E402
from app.database.database import SessionLocal  # noqa: E402
from app.monitor import PrivacyMonitor  # noqa: E402
from app.websocket.manager import ConnectionManager  # noqa: E402


def make_parsed(dst="1.1.1.1", sni=None, service="Unknown", port=443, size=100):
    class P:
        pass

    p = P()
    p.source_ip = "192.168.1.10"
    p.destination_ip = dst
    p.source_port = 50000
    p.destination_port = port
    p.protocol = "TCP"
    p.packet_size = size
    p.direction = "outbound"
    p.encrypted = True
    p.service = service
    p.sni = sni
    return p


class TestFlowEvents:
    def test_process_parsed_returns_new_flag(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        flow1, is_new1 = tracker.process_parsed(make_parsed())
        flow2, is_new2 = tracker.process_parsed(make_parsed())
        assert is_new1 is True
        assert is_new2 is False
        assert flow1 is flow2

    def test_callbacks_fire_without_loop(self):
        """With no running event loop, broadcasts are no-ops (never raise)."""
        events = []
        monitor = PrivacyMonitor()
        capture = PacketCaptureManager(
            on_flow_close=lambda f: events.append(("close", f)),
            on_active_update=lambda f, is_new=False, tick=False: events.append(("update", f, is_new, tick)),
        )
        monitor.capture = capture
        capture.tracker.process_parsed(make_parsed())
        monitor._on_active_update(None, is_new=False, tick=True)  # snapshot broadcast
        # no exception raised


class TestLiveSummary:
    def test_live_summary_includes_active_flows(self):
        monitor = PrivacyMonitor()
        capture = PacketCaptureManager()
        monitor.capture = capture
        capture.tracker.process_parsed(make_parsed(dst="142.250.190.46", size=500))
        db = SessionLocal()
        try:
            summary = monitor._live_summary(db)
        finally:
            db.close()
        assert summary["active_connections"] == 1
        assert summary["bytes_sent"] >= 500
        assert summary["total_connections"] >= 1

    def test_live_payload_carries_website(self):
        monitor = PrivacyMonitor()
        capture = PacketCaptureManager()
        monitor.capture = capture
        capture.dns_cache.record("142.250.190.46", "google.com", ttl=600)
        flow, _ = capture.tracker.process_parsed(
            make_parsed(dst="142.250.190.46", service="HTTPS/TLS")
        )
        assert flow.website == "google.com"
        assert flow.domain == "google.com"
        assert flow.service == "Google"
        assert flow.application == "Unknown"
        payload = monitor.live_payload()
        assert any(c["website"] == "google.com" for c in payload["active_connections"])
        assert any(w["website"] == "google.com" for w in payload["websites"])

    def test_flow_close_persists_website(self):
        monitor = PrivacyMonitor()
        capture = PacketCaptureManager(
            on_flow_close=monitor._on_flow_close,
            on_active_update=monitor._on_active_update,
        )
        monitor.capture = capture
        capture.dns_cache.record("13.107.42.14", "microsoft.com", ttl=600)
        flow, _ = capture.tracker.process_parsed(make_parsed(dst="13.107.42.14"))
        capture.tracker.close_all()
        db = SessionLocal()
        try:
            from app.database import crud

            rows = crud.get_traffic_history(db, limit=5)
        finally:
            db.close()
        assert any(r.website == "microsoft.com" for r in rows)


class TestBroadcastSync:
    def test_noop_without_loop(self):
        manager2 = ConnectionManager()
        manager2._connections = ["sentinel"]
        manager2.broadcast_sync({"type": "live"})  # must not raise

    def test_schedules_on_running_loop(self):
        manager2 = ConnectionManager()
        received = []
        done = threading.Event()

        async def fake_broadcast(message):
            received.append(message)
            done.set()

        manager2.broadcast = fake_broadcast
        manager2._connections = ["sentinel"]

        loop = None

        def run_loop():
            nonlocal loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_forever()

        import asyncio

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
        time.sleep(0.05)
        manager2.set_loop(loop)
        manager2.broadcast_sync({"type": "live", "summary": {}})
        assert done.wait(timeout=2), "broadcast was never delivered"
        assert received == [{"type": "live", "summary": {}}]
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=2)