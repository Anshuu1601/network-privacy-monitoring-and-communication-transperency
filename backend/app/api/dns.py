"""DNS mapping endpoints (in-memory, expiring cache)."""
from fastapi import APIRouter

from app.monitor import monitor

router = APIRouter(prefix="/api/dns", tags=["dns"])


@router.get("/domains")
def dns_domains(limit: int = 100):
    cache = monitor._ensure_capture().dns_cache
    return {
        "count": cache.size(),
        "domains": cache.snapshot(limit=limit),
    }