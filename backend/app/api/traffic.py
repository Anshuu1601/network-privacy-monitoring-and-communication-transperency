"""Live traffic endpoints + real-time snapshot."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analysis.traffic_analyzer import flows_over_time
from app.database import crud
from app.database.database import get_db
from app.database.models import Connection
from app.monitor import monitor
from app.timeutils import to_iso_utc

router = APIRouter(prefix="/api/traffic", tags=["traffic"])


@router.get("/live")
def live_traffic():
    return monitor.live_payload()


@router.get("/summary")
def traffic_summary(db: Session = Depends(get_db)):
    return monitor._live_summary(db)


@router.get("/history")
def traffic_history(
    db: Session = Depends(get_db),
    limit: int = Query(200, ge=1, le=5000),
    device_id: int | None = None,
):
    connections = crud.get_traffic_history(db, limit=limit, device_id=device_id)
    return [
        {
            "id": c.id,
            "timestamp": to_iso_utc(c.timestamp),
            "first_seen": to_iso_utc(c.timestamp),
            "last_seen": to_iso_utc(c.last_seen),
            "device": c.device.name if c.device else None,
            "device_id": c.device_id,
            "source_ip": c.source_ip,
            "destination_ip": c.destination_ip,
            "source_port": c.source_port,
            "destination_port": c.destination_port,
            "protocol": c.protocol,
            "service": c.service,
            "website": c.website,
            "domain": c.domain,
            "application": c.application,
            "encrypted": bool(c.encrypted),
            "bytes_sent": c.bytes_sent,
            "bytes_received": c.bytes_received,
            "packets_sent": c.packets_sent,
            "packets_received": c.packets_received,
            "duration": c.duration,
            "status": c.status,
        }
        for c in connections
    ]


@router.get("/over-time")
def traffic_over_time(
    db: Session = Depends(get_db),
    bucket: int = Query(30, ge=5, le=3600),
    hours: int = Query(24, ge=1, le=168),
):
    from datetime import datetime, timedelta, timezone

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    connections = (
        db.query(Connection)
        .filter(Connection.timestamp >= since)
        .order_by(Connection.timestamp.asc())
        .all()
    )
    return flows_over_time(connections, bucket_seconds=bucket)