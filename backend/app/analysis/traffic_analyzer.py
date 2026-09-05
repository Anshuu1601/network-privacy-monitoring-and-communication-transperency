"""Traffic statistics: upload/download, speeds, protocol and service shares.

All figures derive from flow metadata. Works on aggregated flows so it is
cheap to compute repeatedly for live updates.
"""
import time
from datetime import datetime, timezone

from app.timeutils import to_iso_utc


def sum_bytes(flows) -> dict:
    sent = sum(getattr(f, "bytes_sent", 0) or 0 for f in flows)
    received = sum(getattr(f, "bytes_received", 0) or 0 for f in flows)
    return {"bytes_sent": sent, "bytes_received": received, "total": sent + received}


def compute_throughput(recent_flows, window_seconds: float = 10.0) -> dict:
    """Upload/download speed (bytes/sec) over a sliding window of flows."""
    now = time.time()
    cutoff = now - window_seconds
    window = [f for f in recent_flows if f.last_seen >= cutoff and f.last_seen <= now]
    totals = sum_bytes(window)
    window_secs = max(window_seconds, 1.0)
    return {
        "upload_bps": totals["bytes_sent"] / window_secs,
        "download_bps": totals["bytes_received"] / window_secs,
        "upload_kbps": totals["bytes_sent"] / window_secs / 1024,
        "download_kbps": totals["bytes_received"] / window_secs / 1024,
    }


def flows_over_time(connections, bucket_seconds: float = 30.0) -> list[dict]:
    """Buckets flows into fixed-width time windows for charting."""
    if not connections:
        return []
    buckets: dict[int, dict] = {}
    for conn in connections:
        ts = conn.timestamp
        if ts is None:
            continue
        try:
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            bucket = int(ts.timestamp() // bucket_seconds) * bucket_seconds
        except (AttributeError, OSError):
            continue
        entry = buckets.setdefault(bucket, {"time": bucket, "upload": 0, "download": 0})
        entry["upload"] += conn.bytes_sent or 0
        entry["download"] += conn.bytes_received or 0
    out = sorted(buckets.values(), key=lambda b: b["time"])
    return [
        {
            "time": to_iso_utc(datetime.fromtimestamp(b["time"], tz=timezone.utc)),
            "upload": b["upload"],
            "download": b["download"],
        }
        for b in out
    ]


def protocol_breakdown(protocol_stats: list[dict], total_bytes: int) -> list[dict]:
    rows = []
    for item in protocol_stats:
        proto = item.get("protocol") or "Unknown"
        bytes_val = item.get("bytes") or 0
        rows.append({
            "protocol": proto,
            "count": item.get("count", 0),
            "bytes": bytes_val,
            "percentage": round(bytes_val / total_bytes * 100, 1) if total_bytes else 0.0,
        })
    return rows