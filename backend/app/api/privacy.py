"""Privacy endpoints: score, encryption stats, privacy summary."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analysis.encryption_analyzer import ENC_LABEL_DETECTED, ENC_LABEL_NOT_DETECTED
from app.analysis.privacy_score import compute_privacy_score
from app.database import crud
from app.database.database import get_db
from app.database.models import Connection
from app.monitor import monitor

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/score")
def privacy_score(db: Session = Depends(get_db)):
    summary = crud.get_connection_summary(db)
    unencrypted_row = (
        db.query(func.coalesce(func.sum(Connection.bytes_sent + Connection.bytes_received), 0))
        .filter(Connection.encrypted == 0)
        .scalar()
    )
    score = compute_privacy_score(
        total_connections=summary["total_connections"],
        encrypted_connections=summary["encrypted_connections"],
        unencrypted_bytes=unencrypted_row or 0,
        total_bytes=summary["bytes_sent"] + summary["bytes_received"],
    )
    return score


@router.get("/encryption")
def encryption_stats(db: Session = Depends(get_db)):
    total = db.query(Connection).count()
    encrypted = db.query(Connection).filter(Connection.encrypted == 1).count()
    unencrypted = total - encrypted
    enc_pct = round(encrypted / total * 100, 1) if total else 0.0
    return {
        "total": total,
        "encrypted": encrypted,
        "unencrypted": unencrypted,
        "encrypted_percentage": enc_pct,
        "unencrypted_percentage": round(100.0 - enc_pct, 1),
        "label_detected": ENC_LABEL_DETECTED,
        "label_not_detected": ENC_LABEL_NOT_DETECTED,
    }


@router.get("/summary")
def privacy_summary():
    return monitor.live_payload()