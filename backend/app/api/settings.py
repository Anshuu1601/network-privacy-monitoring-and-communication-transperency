"""Application settings endpoints: score weights, retention, demo toggle."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.database.crud import delete_connections_before
from app.monitor import monitor

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ScoreWeights(BaseModel):
    encryption: float
    protocol: float
    unencrypted_penalty: float


class RetentionRequest(BaseModel):
    days: int | None = None  # None = unlimited


class DemoMode(BaseModel):
    enabled: bool


@router.get("")
def get_settings():
    return {
        "score_weights": settings.SCORE_WEIGHTS,
        "retention_days": settings.RETENTION_DAYS,
        "capture_interface": settings.CAPTURE_INTERFACE,
        "demo_mode": settings.DEMO_MODE,
        "api_host": settings.API_HOST,
        "api_port": settings.API_PORT,
    }


@router.post("/score-weights")
def set_score_weights(payload: ScoreWeights):
    if payload.encryption < 0 or payload.protocol < 0 or payload.unencrypted_penalty < 0:
        raise HTTPException(status_code=400, detail="Weights must be non-negative")
    settings.SCORE_WEIGHTS = {
        "encryption": payload.encryption,
        "protocol": payload.protocol,
        "unencrypted_penalty": payload.unencrypted_penalty,
    }
    return settings.SCORE_WEIGHTS


@router.post("/demo")
def set_demo_mode(payload: DemoMode):
    monitor.set_demo_mode(payload.enabled)
    return {"demo_mode": payload.enabled}


@router.post("/retention")
def set_retention(payload: RetentionRequest):
    if payload.days is not None and payload.days < 1:
        raise HTTPException(status_code=400, detail="Retention days must be positive")
    settings.RETENTION_DAYS = payload.days or 0
    return {"retention_days": settings.RETENTION_DAYS}


@router.post("/retention/clear")
def clear_old_data(db: Session = Depends(get_db), days: int | None = None):
    """Clear data older than the retention period (or an explicit day count).

    Requires confirmation from the frontend before calling.
    """
    from datetime import datetime, timedelta, timezone

    from app.timeutils import to_iso_utc

    days = days or settings.RETENTION_DAYS
    if days <= 0:
        raise HTTPException(status_code=400, detail="Unlimited retention: specify a day count to clear")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted = delete_connections_before(db, cutoff)
    return {"deleted": deleted, "cutoff": to_iso_utc(cutoff)}