"""Privacy alert endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import crud
from app.database.database import get_db
from app.timeutils import to_iso_utc

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=500)):
    return [
        {
            "id": a.id,
            "timestamp": to_iso_utc(a.timestamp),
            "type": a.type,
            "message": a.message,
            "severity": a.severity,
            "status": a.status,
        }
        for a in crud.get_recent_alerts(db, limit=limit)
    ]


@router.get("/unencrypted")
def unencrypted_alerts(db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=500)):
    alerts = [
        a
        for a in crud.get_recent_alerts(db, limit=max(limit * 2, 100))
        if a.type == "unencrypted"
    ]
    return [
        {
            "id": a.id,
            "timestamp": to_iso_utc(a.timestamp),
            "type": a.type,
            "message": a.message,
            "severity": a.severity,
            "status": a.status,
        }
        for a in alerts[:limit]
    ]