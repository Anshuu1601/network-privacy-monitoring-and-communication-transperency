"""SQLAlchemy ORM models.

The application only stores network *metadata*. Payloads, bodies, cookies,
messages and other private content are never stored or transmitted.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


def utcnow():
    """Naive UTC timestamp. SQLite stores no timezone; keeping timestamps
    naive UTC avoids offset-aware vs offset-naive comparison errors."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, default="My Laptop")
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    mac_address = Column(String(32), nullable=True)
    interface = Column(String(128), nullable=True)
    is_local = Column(Integer, default=1)
    first_seen = Column(DateTime, default=utcnow)
    last_seen = Column(DateTime, default=utcnow)

    connections = relationship("Connection", back_populates="device")

    __table_args__ = (Index("ix_devices_ip", "ip_address"),)


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    timestamp = Column(DateTime, default=utcnow, index=True)
    source_ip = Column(String(64), nullable=True)
    destination_ip = Column(String(64), nullable=True, index=True)
    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True, index=True)
    protocol = Column(String(16), nullable=True, index=True)
    service = Column(String(128), nullable=True, index=True)
    website = Column(String(255), nullable=True, index=True)
    domain = Column(String(255), nullable=True)
    application = Column(String(128), nullable=True, index=True)
    encrypted = Column(Integer, default=0, index=True)
    bytes_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    packets_sent = Column(Integer, default=0)
    packets_received = Column(Integer, default=0)
    duration = Column(Float, default=0.0)
    status = Column(String(32), default="active")
    last_seen = Column(DateTime, default=utcnow)

    device = relationship("Device", back_populates="connections")
    alerts = relationship("Alert", back_populates="connection")

    __table_args__ = (
        Index("ix_connections_device_time", "device_id", "timestamp"),
        Index("ix_connections_time", "timestamp"),
        Index("ix_connections_device_proto", "device_id", "protocol"),
    )


class PrivacyScore(Base):
    __tablename__ = "privacy_scores"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    timestamp = Column(DateTime, default=utcnow, index=True)
    score = Column(Integer, default=0)
    encrypted_percentage = Column(Float, default=0.0)
    unencrypted_percentage = Column(Float, default=0.0)
    reasons = Column(Text, default="")

    __table_args__ = (Index("ix_scores_device_time", "device_id", "timestamp"),)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=True)
    timestamp = Column(DateTime, default=utcnow, index=True)
    type = Column(String(64), default="unencrypted")
    message = Column(String(512), nullable=False)
    severity = Column(String(16), default="WARNING")
    status = Column(String(16), default="new")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)

    connection = relationship("Connection", back_populates="alerts")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    report_type = Column(String(32), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    file_path = Column(String(512), nullable=True)
    format = Column(String(16), default="pdf")
    created_at = Column(DateTime, default=utcnow)
