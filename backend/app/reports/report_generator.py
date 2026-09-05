"""Report generation (daily/weekly summary data) and aggregation helpers."""
import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analysis.privacy_score import compute_privacy_score
from app.database import crud
from app.database.models import Connection, Device
from app.timeutils import to_iso_utc

logger = logging.getLogger("privacy.reports")


def _naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _day_range(day: date):
    start = _naive(datetime.combine(day, time.min, tzinfo=timezone.utc))
    end = _naive(datetime.combine(day, time.max, tzinfo=timezone.utc))
    return start, end


def _date_range(start: date, end: date):
    start_dt = _naive(datetime.combine(start, time.min, tzinfo=timezone.utc))
    end_dt = _naive(datetime.combine(end, time.max, tzinfo=timezone.utc))
    return start_dt, end_dt


def _summarize(db: Session, start_dt: datetime, end_dt: datetime, devices: list[Device]) -> dict:
    connections = (
        db.query(Connection)
        .filter(Connection.timestamp >= start_dt, Connection.timestamp <= end_dt)
        .all()
    )
    total = len(connections)
    encrypted = sum(1 for c in connections if c.encrypted)
    sent = sum(c.bytes_sent or 0 for c in connections)
    received = sum(c.bytes_received or 0 for c in connections)
    unencrypted_bytes = sum(
        (c.bytes_sent or 0) + (c.bytes_received or 0)
        for c in connections if not c.encrypted
    )
    total_bytes = sent + received

    score_result = compute_privacy_score(
        total_connections=total,
        encrypted_connections=encrypted,
        unencrypted_bytes=unencrypted_bytes,
        total_bytes=total_bytes,
    )

    services = []
    if connections:
        buckets: dict[str, dict] = {}
        for c in connections:
            name = c.service or "Other"
            bucket = buckets.setdefault(name, {"service": name, "bytes": 0, "count": 0})
            bucket["bytes"] += (c.bytes_sent or 0) + (c.bytes_received or 0)
            bucket["count"] += 1
        services = sorted(buckets.values(), key=lambda b: b["bytes"], reverse=True)[:8]

    alerts = crud.get_recent_alerts(db, limit=20)
    alerts_in_range = [
        a for a in alerts if start_dt <= a.timestamp <= end_dt
    ]

    return {
        "start_time": to_iso_utc(start_dt),
        "end_time": to_iso_utc(end_dt),
        "timezone": "UTC",
        "total_connections": total,
        "encrypted_connections": encrypted,
        "unencrypted_connections": total - encrypted,
        "encrypted_percentage": round(encrypted / total * 100, 1) if total else 0.0,
        "bytes_sent": sent,
        "bytes_received": received,
        "total_bytes": total_bytes,
        "privacy_score": score_result,
        "services": services,
        "alerts": [
            {
                "timestamp": to_iso_utc(a.timestamp),
                "severity": a.severity,
                "message": a.message,
                "status": a.status,
            }
            for a in alerts_in_range
        ],
        "devices": [
            {
                "id": d.id,
                "name": d.name,
                "ip_address": d.ip_address,
                "interface": d.interface,
            }
            for d in devices
        ],
    }


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def daily_report(db: Session, day: date | None = None) -> dict:
    day = day or _today_utc()
    start, end = _day_range(day)
    devices = db.query(Device).all()
    summary = _summarize(db, start, end, devices)
    summary["report_type"] = "daily"
    summary["period_label"] = day.isoformat()
    summary["daily_traffic"] = []
    return summary


def weekly_report(db: Session, week_end: date | None = None) -> dict:
    end = week_end or _today_utc()
    start = end - __import__("datetime").timedelta(days=6)
    start_dt, end_dt = _date_range(start, end)
    devices = db.query(Device).all()
    summary = _summarize(db, start_dt, end_dt, devices)
    summary["report_type"] = "weekly"
    summary["period_label"] = f"{start.isoformat()} to {end.isoformat()}"

    daily = []
    from datetime import timedelta

    for i in range(7):
        d = start + timedelta(days=i)
        s, e = _day_range(d)
        day_conns = (
            db.query(Connection)
            .filter(Connection.timestamp >= s, Connection.timestamp <= e)
            .all()
        )
        if not day_conns:
            continue
        day_total = len(day_conns)
        day_enc = sum(1 for c in day_conns if c.encrypted)
        day_sent = sum(c.bytes_sent or 0 for c in day_conns)
        day_received = sum(c.bytes_received or 0 for c in day_conns)
        day_score = compute_privacy_score(
            total_connections=day_total,
            encrypted_connections=day_enc,
            unencrypted_bytes=sum(
                (c.bytes_sent or 0) + (c.bytes_received or 0) for c in day_conns if not c.encrypted
            ),
            total_bytes=day_sent + day_received,
        )
        daily.append({
            "date": d.isoformat(),
            "connections": day_total,
            "encrypted_percentage": round(day_enc / day_total * 100, 1) if day_total else 0.0,
            "bytes_sent": day_sent,
            "bytes_received": day_received,
            "privacy_score": day_score["score"],
        })
    summary["daily_traffic"] = daily
    return summary


def custom_range_report(db: Session, start: date, end: date) -> dict:
    if start > end:
        start, end = end, start
    start_dt, end_dt = _date_range(start, end)
    devices = db.query(Device).all()
    summary = _summarize(db, start_dt, end_dt, devices)
    summary["report_type"] = "custom"
    summary["period_label"] = f"{start.isoformat()} to {end.isoformat()}"
    return summary