"""Short-lived DNS mapping cache (IP → domain).

Privacy: the cache is memory-only, expires entries quickly (TTL honored,
default from settings.DNS_CACHE_TTL_SECONDS) and never stores query content.
Mappings are best-effort metadata derived from observable DNS responses.
"""
import threading
import time

from app.config import settings


class DnsCache:
    def __init__(self, default_ttl: int | None = None, max_entries: int = 2048):
        self._default_ttl = default_ttl or int(settings.DNS_CACHE_TTL_SECONDS)
        self._max_entries = max_entries
        self._entries: dict[str, dict] = {}
        self._lock = threading.Lock()

    def record(self, ip: str, domain: str, ttl: int | None = None) -> None:
        if not ip or not domain:
            return
        now = time.time()
        expires = now + (int(ttl) if ttl is not None else self._default_ttl)
        if expires <= now:
            # TTL 0 means "do not cache" — store nothing.
            return
        with self._lock:
            existing = self._entries.get(ip)
            if existing:
                existing["domain"] = domain
                existing["last_seen"] = now
                existing["expires_at"] = max(existing.get("expires_at", 0), expires)
            else:
                if len(self._entries) >= self._max_entries:
                    self._evict_oldest()
                self._entries[ip] = {
                    "domain": domain,
                    "first_seen": now,
                    "last_seen": now,
                    "expires_at": expires,
                }

    def lookup(self, ip: str) -> str | None:
        """Return the domain for an IP, or None if unknown/expired."""
        if not ip:
            return None
        now = time.time()
        with self._lock:
            entry = self._entries.get(ip)
            if entry is None:
                return None
            if entry["expires_at"] < now:
                del self._entries[ip]
                return None
            return entry["domain"]

    def expire_stale(self) -> int:
        now = time.time()
        with self._lock:
            stale = [ip for ip, e in self._entries.items() if e["expires_at"] < now]
            for ip in stale:
                del self._entries[ip]
        return len(stale)

    def _evict_oldest(self):
        if not self._entries:
            return
        oldest = min(self._entries, key=lambda ip: self._entries[ip]["last_seen"])
        del self._entries[oldest]

    def snapshot(self, limit: int = 100) -> list[dict]:
        now = time.time()
        with self._lock:
            entries = [
                {
                    "ip": ip,
                    "domain": e["domain"],
                    "first_seen": e["first_seen"],
                    "last_seen": e["last_seen"],
                    "expires_at": e["expires_at"],
                    "ttl_remaining": max(0, round(e["expires_at"] - now, 1)),
                }
                for ip, e in self._entries.items()
                if e["expires_at"] >= now
            ]
        entries.sort(key=lambda e: e["last_seen"], reverse=True)
        return entries[:limit]

    def size(self) -> int:
        with self._lock:
            return len(self._entries)