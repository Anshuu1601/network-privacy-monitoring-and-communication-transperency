"""CSV and PDF export for connection history and reports."""
import csv
import io
import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import Connection
from app.reports.report_generator import custom_range_report, daily_report, weekly_report
from app.timeutils import to_iso_utc

logger = logging.getLogger("privacy.reports")

CSV_COLUMNS = [
    "timestamp", "device", "source_ip", "destination_ip",
    "source_port", "destination_port", "protocol", "service",
    "encrypted", "bytes_sent", "bytes_received", "duration",
]


def _rows_from_connections(db: Session) -> list[dict]:
    connections = db.query(Connection).order_by(Connection.timestamp.desc()).all()
    rows = []
    for c in connections:
        device_name = c.device.name if c.device else "Unknown"
        rows.append({
            "timestamp": to_iso_utc(c.timestamp) or "",
            "device": device_name,
            "source_ip": c.source_ip or "",
            "destination_ip": c.destination_ip or "",
            "source_port": c.source_port if c.source_port is not None else "",
            "destination_port": c.destination_port if c.destination_port is not None else "",
            "protocol": c.protocol or "",
            "service": c.service or "",
            "encrypted": c.encrypted or 0,
            "bytes_sent": c.bytes_sent or 0,
            "bytes_received": c.bytes_received or 0,
            "duration": round(c.duration or 0.0, 2),
        })
    return rows


def export_connections_csv(db: Session) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for row in _rows_from_connections(db):
        writer.writerow(row)
    return buffer.getvalue()


def build_report_data(db: Session, report_type: str = "daily", start=None, end=None) -> dict:
    if report_type == "daily":
        return daily_report(db)
    if report_type == "weekly":
        return weekly_report(db)
    if report_type == "custom":
        if not start or not end:
            raise HTTPException(status_code=400, detail="Custom report requires start and end dates")
        return custom_range_report(db, start, end)
    raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")


def _fmt_bytes(n: int) -> str:
    n = n or 0
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _summary_lines(data: dict) -> list[tuple[str, str]]:
    score = data.get("privacy_score", {})
    lines = [
        ("Period", data.get("period_label", "")),
        ("Total Connections", str(data.get("total_connections", 0))),
        ("Encrypted Connections", str(data.get("encrypted_connections", 0))),
        ("Unencrypted Connections", str(data.get("unencrypted_connections", 0))),
        ("Encryption", f"{data.get('encrypted_percentage', 0)}%"),
        ("Total Upload", _fmt_bytes(data.get("bytes_sent", 0))),
        ("Total Download", _fmt_bytes(data.get("bytes_received", 0))),
        ("Privacy Score", f"{score.get('score', 0)}/100"),
    ]
    return lines


def export_report_pdf(data: dict) -> bytes:
    """Generate a professional PDF report using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError as exc:  # pragma: no cover
        logger.error("ReportLab not installed: %s", exc)
        raise HTTPException(status_code=500, detail="PDF support not available (reportlab not installed)")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.7 * inch, leftMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=18, spaceAfter=4,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], fontSize=10,
        textColor=colors.HexColor("#64748b"), spaceAfter=12,
    )
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)

    story = []
    report_type = data.get("report_type", "report").capitalize()
    tz_label = data.get("timezone", "UTC")
    story.append(Paragraph("Network Privacy Monitoring & Communication Transparency Dashboard", title_style))
    story.append(Paragraph(f"{report_type} Network Privacy Report", subtitle))
    story.append(Paragraph(f"Reporting period: {data.get('period_label', '')}", subtitle))
    story.append(Paragraph(f"Timezone: {tz_label} (all timestamps in this report are UTC)", subtitle))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Summary", h2))
    table_data = [[Paragraph("<b>Metric</b>", body), Paragraph("<b>Value</b>", body)]]
    for label, value in _summary_lines(data):
        table_data.append([Paragraph(label, body), Paragraph(value, body)])
    summary_table = Table(table_data, colWidths=[3 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(summary_table)

    score = data.get("privacy_score", {})
    reasons = score.get("reasons", [])
    if reasons:
        story.append(Paragraph("Privacy Score Breakdown", h2))
        for reason in reasons:
            story.append(Paragraph(reason, body))

    services = data.get("services", [])
    if services:
        story.append(Paragraph("Top Services", h2))
        svc_data = [[Paragraph("<b>Service</b>", body), Paragraph("<b>Connections</b>", body), Paragraph("<b>Data</b>", body)]]
        for s in services[:8]:
            svc_data.append([
                Paragraph(str(s.get("service", "Other")), body),
                Paragraph(str(s.get("count", 0)), body),
                Paragraph(_fmt_bytes(s.get("bytes", 0)), body),
            ])
        svc_table = Table(svc_data, colWidths=[2 * inch, 1.5 * inch, 2.5 * inch])
        svc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ]))
        story.append(svc_table)

    alerts = data.get("alerts", [])
    if alerts:
        story.append(Paragraph("Privacy Alerts", h2))
        alert_lines = []
        for a in alerts[:10]:
            alert_lines.append(Paragraph(
                f"• [{a.get('severity', 'WARNING')}] {a.get('message', '')} ({a.get('timestamp', '')})",
                body,
            ))
        story.extend(alert_lines)
    else:
        story.append(Paragraph("No unencrypted communication events recorded.", body))

    daily = data.get("daily_traffic", [])
    if daily and data.get("report_type") == "weekly":
        story.append(Paragraph("Daily Traffic", h2))
        day_data = [[Paragraph("<b>Date</b>", body), Paragraph("<b>Connections</b>", body),
                     Paragraph("<b>Upload</b>", body), Paragraph("<b>Download</b>", body),
                     Paragraph("<b>Privacy Score</b>", body)]]
        for d in daily:
            day_data.append([
                Paragraph(str(d.get("date", "")), body),
                Paragraph(str(d.get("connections", 0)), body),
                Paragraph(_fmt_bytes(d.get("bytes_sent", 0)), body),
                Paragraph(_fmt_bytes(d.get("bytes_received", 0)), body),
                Paragraph(str(d.get("privacy_score", 0)), body),
            ])
        day_table = Table(day_data, colWidths=[1.2 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.5 * inch])
        day_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ]))
        story.append(day_table)

    devices = data.get("devices", [])
    if devices:
        story.append(Paragraph("Monitored Devices", h2))
        for d in devices:
            story.append(Paragraph(
                f"• {d.get('name', '')} ({d.get('ip_address', '')}) — interface: {d.get('interface', 'N/A')}",
                body,
            ))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "This report analyzes network metadata for privacy visibility. It does not decrypt "
        "or store private communication content.",
        ParagraphStyle("Footer", parent=body, fontSize=8, textColor=colors.HexColor("#94a3b8")),
    ))

    doc.build(story)
    return buffer.getvalue()