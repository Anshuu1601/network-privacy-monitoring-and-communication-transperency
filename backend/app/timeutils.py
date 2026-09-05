"""Shared timestamp helpers enforcing a single timezone strategy.

Contract:
  - Capture / flow timing: the actual packet capture time (aware UTC).
  - Database (SQLite): naive UTC datetimes (SQLite has no timezone support).
  - API / WebSocket / CSV / reports: ISO-8601 UTC strings ending in ``Z``.
  - Frontend: converts the UTC string to the browser's local timezone once.

A timestamp flows: capture time -> stored as UTC -> returned as UTC -> converted
once for display. It is never converted through local time on the backend.
"""
from datetime import datetime, timezone


def utc_now_naive() -> datetime:
    """Current time as a naive UTC datetime (matching SQLAlchemy storage)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_iso() -> str:
    return to_iso_utc(datetime.now(timezone.utc))


def from_unix(ts: float) -> datetime:
    """Convert a Unix epoch timestamp to an aware UTC datetime."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def to_naive_utc(dt: datetime | None) -> datetime | None:
    """Normalize any datetime to a naive UTC datetime for storage."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt  # already naive; assumed UTC


def to_iso_utc(dt: datetime | None) -> str | None:
    """Serialize a datetime as ISO-8601 UTC with an explicit ``Z`` suffix.

    Naive datetimes are interpreted as UTC (the storage convention).
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")