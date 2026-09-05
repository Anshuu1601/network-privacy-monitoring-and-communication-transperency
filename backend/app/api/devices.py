"""Device endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.traffic_analyzer import flows_over_time
from app.database import crud
from app.database.database import get_db
from app.database.models import Connection, Device
from app.timeutils import to_iso_utc

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
def list_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).order_by(Device.is_local.desc()).all()
    return [crud.get_device_stats(db, d) for d in devices]


@router.get("/{device_id}")
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return crud.get_device_stats(db, device)


@router.get("/{device_id}/traffic")
def device_traffic(
    device_id: int,
    db: Session = Depends(get_db),
    limit: int = 200,
    bucket: int = 30,
):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    connections = crud.get_traffic_history(db, limit=limit, device_id=device_id)
    history = [
        {
            "id": c.id,
            "timestamp": to_iso_utc(c.timestamp),
            "first_seen": to_iso_utc(c.timestamp),
            "last_seen": to_iso_utc(c.last_seen),
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
            "duration": c.duration,
            "status": c.status,
        }
        for c in connections
    ]
    return {
        "device": crud.get_device_stats(db, device),
        "connections": history,
        "over_time": flows_over_time(connections, bucket_seconds=bucket),
    }