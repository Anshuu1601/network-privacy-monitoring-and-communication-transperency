"""Report generation and export endpoints."""
import logging
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.database.models import Report
from app.reports.export import (
    build_report_data,
    export_connections_csv,
    export_report_pdf,
)
from app.timeutils import to_iso_utc

logger = logging.getLogger("privacy.reports")

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _serialize(data: dict) -> dict:
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean(i) for i in obj]
        if isinstance(obj, datetime):
            return to_iso_utc(obj)
        if isinstance(obj, date):
            return obj.isoformat()
        return obj

    return clean(data)


@router.get("/daily")
def get_daily_report(db: Session = Depends(get_db)):
    try:
        return _serialize(build_report_data(db, "daily"))
    except Exception as exc:
        logger.error("Daily report failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate daily report")


@router.get("/weekly")
def get_weekly_report(db: Session = Depends(get_db)):
    try:
        return _serialize(build_report_data(db, "weekly"))
    except Exception as exc:
        logger.error("Weekly report failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate weekly report")


@router.get("/custom")
def get_custom_report(
    db: Session = Depends(get_db),
    start: date = Query(..., description="Start date YYYY-MM-DD"),
    end: date = Query(..., description="End date YYYY-MM-DD"),
):
    try:
        return _serialize(build_report_data(db, "custom", start=start, end=end))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Custom report failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate custom report")


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    try:
        csv_content = export_connections_csv(db)
    except Exception as exc:
        logger.error("CSV export failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to export CSV")
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=connection_history.csv"},
    )


@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db),
    report_type: str = Query("daily", pattern="^(daily|weekly|custom)$"),
    start: date | None = Query(None),
    end: date | None = Query(None),
):
    try:
        data = build_report_data(db, report_type, start=start, end=end)
        pdf_bytes = export_report_pdf(data)
        _record_report(db, report_type, data, settings.REPORT_DIR, len(pdf_bytes))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("PDF export failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={report_type}_report.pdf"
        },
    )


def _record_report(db: Session, report_type: str, data: dict, report_dir: Path, size: int):
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc)
    filename = f"{report_type}_report_{ts.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = report_dir / filename
    report = Report(
        report_type=report_type,
        start_time=ts,
        end_time=ts,
        file_path=str(file_path),
        format="pdf",
    )
    db.add(report)
    db.commit()