"""DNS cache tests: mapping, lookup, expiry, snapshot."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.analysis.dns_cache import DnsCache  # noqa: E402


class TestDnsCache:
    def test_record_and_lookup(self):
        cache = DnsCache(default_ttl=300)
        cache.record("142.250.190.46", "google.com", ttl=300)
        assert cache.lookup("142.250.190.46") == "google.com"

    def test_unknown_ip_returns_none(self):
        cache = DnsCache(default_ttl=300)
        assert cache.lookup("8.8.8.8") is None

    def test_ignores_empty(self):
        cache = DnsCache(default_ttl=300)
        cache.record("", "google.com")
        cache.record("1.1.1.1", "")
        assert cache.size() == 0

    def test_expiry(self):
        cache = DnsCache(default_ttl=0)  # expires immediately
        cache.record("1.2.3.4", "example.com", ttl=0)
        assert cache.lookup("1.2.3.4") is None
        assert cache.size() == 0

    def test_expire_stale_removes_entries(self):
        cache = DnsCache(default_ttl=300)
        cache.record("1.2.3.4", "a.com", ttl=1)
        cache.record("5.6.7.8", "b.com", ttl=300)
        time.sleep(1.1)
        cache.expire_stale()
        assert cache.lookup("1.2.3.4") is None
        assert cache.lookup("5.6.7.8") == "b.com"

    def test_ttl_honored_from_record(self):
        cache = DnsCache(default_ttl=300)
        cache.record("9.9.9.9", "dns9.com", ttl=0)
        assert cache.lookup("9.9.9.9") is None

    def test_snapshot(self):
        cache = DnsCache(default_ttl=300)
        cache.record("1.1.1.1", "one.com")
        cache.record("2.2.2.2", "two.com")
        snap = cache.snapshot()
        domains = {e["domain"] for e in snap}
        assert domains == {"one.com", "two.com"}
        assert all("ttl_remaining" in e for e in snap)

    def test_upgrade_refreshes_expiry(self):
        cache = DnsCache(default_ttl=60)
        cache.record("1.2.3.4", "a.com", ttl=60)
        cache.record("1.2.3.4", "b.com", ttl=60)
        assert cache.lookup("1.2.3.4") == "b.com"
        assert cache.size() == 1