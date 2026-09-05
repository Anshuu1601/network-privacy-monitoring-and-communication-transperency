"""Database access helpers (CRUD)."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import Alert, Connection, Device, PrivacyScore, Report
from app.timeutils import to_iso_utc, utc_now_naive


def get_or_create_device(db: Session, ip: str, name: str = "My Laptop", hostname: str = None,
                         interface: str = None, mac_address: str = None) -> Device:
    if not ip:
        device = db.query(Device).filter(Device.is_local == 1).first()
        if device:
            return device
        device = Device(name=name, hostname=hostname, ip_address=ip,
                        interface=interface, mac_address=mac_address, is_local=1)
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    device = db.query(Device).filter(Device.ip_address == ip).first()
    if not device:
        device = Device(name=name, hostname=hostname, ip_address=ip,
                        interface=interface, mac_address=mac_address, is_local=1)
        db.add(device)
        db.commit()
        db.refresh(device)
    else:
        device.last_seen = utc_now_naive()
        db.commit()
    return device


def create_connection(db: Session, device_id: int, **fields) -> Connection:
    conn = Connection(device_id=device_id, **fields)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def update_connection(db: Session, conn: Connection, **fields) -> Connection:
    for key, value in fields.items():
        setattr(conn, key, value)
    db.commit()
    db.refresh(conn)
    return conn


def close_connection(db: Session, conn: Connection, duration: Optional[float] = None):
    conn.status = "closed"
    if duration is not None:
        conn.duration = duration
    conn.last_seen = utc_now_naive()
    db.commit()
    db.refresh(conn)


def create_privacy_score(db: Session, device_id: int, score: int,
                         encrypted_percentage: float, unencrypted_percentage: float,
                         reasons: str) -> PrivacyScore:
    record = PrivacyScore(
        device_id=device_id,
        score=score,
        encrypted_percentage=encrypted_percentage,
        unencrypted_percentage=unencrypted_percentage,
        reasons=reasons,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_alert(db: Session, message: str, severity: str = "WARNING",
                 connection_id: Optional[int] = None, device_id: Optional[int] = None,
                 alert_type: str = "unencrypted") -> Alert:
    alert = Alert(
        message=message,
        severity=severity,
        connection_id=connection_id,
        device_id=device_id,
        type=alert_type,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_active_connections(db: Session) -> int:
    return db.query(Connection).filter(Connection.status == "active").count()


def get_total_connections(db: Session) -> int:
    return db.query(Connection).count()


def get_connection_summary(db: Session):
    total = db.query(func.count(Connection.id)).scalar() or 0
    encrypted = db.query(Connection).filter(Connection.encrypted == 1).count()
    unencrypted = total - encrypted
    sent = db.query(func.coalesce(func.sum(Connection.bytes_sent), 0)).scalar() or 0
    received = db.query(func.coalesce(func.sum(Connection.bytes_received), 0)).scalar() or 0
    active = get_active_connections(db)
    return {
        "total_connections": total,
        "encrypted_connections": encrypted,
        "unencrypted_connections": unencrypted,
        "bytes_sent": sent,
        "bytes_received": received,
        "active_connections": active,
        "encrypted_percentage": round(encrypted / total * 100, 1) if total else 0.0,
    }


def get_recent_alerts(db: Session, limit: int = 20) -> list[Alert]:
    return (
        db.query(Alert)
        .order_by(Alert.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_services(db: Session, limit: int = 10, start_time: datetime = None,
                 end_time: datetime = None) -> list:
    query = db.query(
        Connection.service,
        func.count(Connection.id).label("count"),
        func.sum(Connection.bytes_sent + Connection.bytes_received).label("bytes"),
    )
    if start_time:
        query = query.filter(Connection.timestamp >= start_time)
    if end_time:
        query = query.filter(Connection.timestamp <= end_time)
    rows = (
        query.filter(Connection.service.isnot(None))
        .group_by(Connection.service)
        .order_by(func.sum(Connection.bytes_sent + Connection.bytes_received).desc())
        .limit(limit)
        .all()
    )
    return [
        {"service": r.service, "count": r.count, "bytes": r.bytes or 0}
        for r in rows
    ]


def get_protocol_traffic(db: Session, start_time: datetime = None, end_time: datetime = None) -> list:
    query = db.query(
        Connection.protocol,
        func.count(Connection.id).label("count"),
        func.sum(Connection.bytes_sent + Connection.bytes_received).label("bytes"),
    )
    if start_time:
        query = query.filter(Connection.timestamp >= start_time)
    if end_time:
        query = query.filter(Connection.timestamp <= end_time)
    rows = (
        query.group_by(Connection.protocol)
        .order_by(func.sum(Connection.bytes_sent + Connection.bytes_received).desc())
        .all()
    )
    return [{"protocol": r.protocol, "count": r.count, "bytes": r.bytes or 0} for r in rows]


def get_websites(db: Session, limit: int = 10, start_time: datetime = None,
                 end_time: datetime = None) -> list:
    """Top websites by transferred bytes. Rows with no website or a generic
    "Unknown" label are excluded."""
    query = db.query(
        Connection.website,
        func.count(Connection.id).label("count"),
        func.sum(Connection.bytes_sent + Connection.bytes_received).label("bytes"),
    )
    if start_time:
        query = query.filter(Connection.timestamp >= start_time)
    if end_time:
        query = query.filter(Connection.timestamp <= end_time)
    rows = (
        query.filter(Connection.website.isnot(None))
        .filter(Connection.website != "")
        .filter(Connection.website != "Unknown")
        .group_by(Connection.website)
        .order_by(func.sum(Connection.bytes_sent + Connection.bytes_received).desc())
        .limit(limit)
        .all()
    )
    return [
        {"website": r.website, "count": r.count, "bytes": r.bytes or 0}
        for r in rows
    ]


def get_traffic_history(db: Session, limit: int = 200, device_id: Optional[int] = None) -> list[Connection]:
    query = db.query(Connection)
    if device_id:
        query = query.filter(Connection.device_id == device_id)
    return (
        query.order_by(Connection.timestamp.desc())
        .limit(limit)
        .all()
    )


def delete_connections_before(db: Session, cutoff: datetime) -> int:
    deleted = (
        db.query(Connection)
        .filter(Connection.timestamp < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def get_device_stats(db: Session, device: Device):
    sent = db.query(func.coalesce(func.sum(Connection.bytes_sent), 0)).filter(Connection.device_id == device.id).scalar() or 0
    received = db.query(func.coalesce(func.sum(Connection.bytes_received), 0)).filter(Connection.device_id == device.id).scalar() or 0
    total = db.query(Connection).filter(Connection.device_id == device.id).count()
    encrypted = db.query(Connection).filter(
        Connection.device_id == device.id, Connection.encrypted == 1
    ).count()
    active = db.query(Connection).filter(
        Connection.device_id == device.id, Connection.status == "active"
    ).count()
    encrypted_pct = round(encrypted / total * 100, 1) if total else 0.0
    return {
        "id": device.id,
        "name": device.name,
        "hostname": device.hostname,
        "ip_address": device.ip_address,
        "mac_address": device.mac_address,
        "interface": device.interface,
        "is_local": device.is_local,
        "first_seen": to_iso_utc(device.first_seen),
        "last_seen": to_iso_utc(device.last_seen),
        "bytes_sent": sent,
        "bytes_received": received,
        "total_connections": total,
        "encrypted_connections": encrypted,
        "encrypted_percentage": encrypted_pct,
        "active_connections": active,
    }
