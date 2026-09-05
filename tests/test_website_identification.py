"""Website identification tests: priority chain + application Unknown."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.analysis.dns_cache import DnsCache  # noqa: E402
from app.analysis.service_identifier import (  # noqa: E402
    extract_registered_domain,
    service_from_domain,
    service_from_flow,
)
from app.analysis.website_identifier import apply_website_to_flow, resolve_website  # noqa: E402
from app.capture.packet_capture import Flow, FlowKey  # noqa: E402


def make_parsed(dst="1.1.1.1", sni=None, service="Unknown"):
    class P:
        pass

    p = P()
    p.source_ip = "192.168.1.10"
    p.destination_ip = dst
    p.source_port = 50000
    p.destination_port = 443
    p.protocol = "TCP"
    p.packet_size = 100
    p.direction = "outbound"
    p.encrypted = True
    p.service = service
    p.sni = sni
    return p


def make_flow():
    return Flow(
        key=FlowKey("192.168.1.10", "1.1.1.1", 50000, 443, "TCP"),
        start_time=0.0,
        last_seen=0.0,
    )


class TestResolutionPriority:
    def test_sni_wins_over_dns(self):
        cache = DnsCache(default_ttl=300)
        cache.record("1.1.1.1", "dns.example.com")
        parsed = make_parsed(sni="real.example.com")
        assert resolve_website(parsed, cache) == "real.example.com"

    def test_dns_wins_over_ip(self):
        cache = DnsCache(default_ttl=300)
        cache.record("1.1.1.1", "mapped.example.com")
        parsed = make_parsed()
        assert resolve_website(parsed, cache) == "mapped.example.com"

    def test_ip_fallback(self):
        parsed = make_parsed(dst="1.1.1.1")
        assert resolve_website(parsed, None) == "1.1.1.1"

    def test_unknown_when_no_signal(self):
        class P:
            destination_ip = None
            sni = None
            service = None

        assert resolve_website(P(), None) == "Unknown"

    def test_sni_not_downgraded_by_dns(self):
        cache = DnsCache(default_ttl=300)
        flow = make_flow()
        apply_website_to_flow(flow, make_parsed(sni="sni.example.com"), cache)
        assert flow.website == "sni.example.com"
        # DNS-only upgrade must not downgrade the SNI result
        cache.record("1.1.1.1", "dns.example.com")
        apply_website_to_flow(flow, make_parsed(sni=None), cache)
        assert flow.website == "sni.example.com"

    def test_dns_upgrades_ip(self):
        cache = DnsCache(default_ttl=300)
        flow = make_flow()
        apply_website_to_flow(flow, make_parsed(dst="1.1.1.1"), cache)
        assert flow.website == "1.1.1.1"
        cache.record("1.1.1.1", "mapped.example.com")
        apply_website_to_flow(flow, make_parsed(dst="1.1.1.1"), cache)
        assert flow.website == "mapped.example.com"

    def test_domain_extracted(self):
        cache = DnsCache(default_ttl=300)
        flow = make_flow()
        apply_website_to_flow(flow, make_parsed(sni="www.github.com"), cache)
        assert flow.domain == "github.com"


class TestApplicationNeverGuessed:
    def test_application_stays_unknown(self):
        cache = DnsCache(default_ttl=300)
        cache.record("1.1.1.1", "youtube.com")
        flow = make_flow()
        apply_website_to_flow(flow, make_parsed(dst="1.1.1.1"), cache)
        assert flow.application == "Unknown"


class TestServiceFromDomain:
    def test_friendly_service(self):
        assert service_from_domain("www.google.com") == "Google"
        assert service_from_domain("youtube.com") == "YouTube"
        assert service_from_domain("api.github.com") == "GitHub"

    def test_unknown_domain(self):
        assert service_from_domain("totally-random-site.example") is None

    def test_ip_no_service(self):
        assert service_from_domain("1.1.1.1") is None

    def test_registered_domain(self):
        assert extract_registered_domain("a.b.google.com") == "google.com"
        assert extract_registered_domain("news.bbc.co.uk") == "bbc.co.uk"
        assert extract_registered_domain("1.1.1.1") == "1.1.1.1"

    def test_service_from_flow_with_website(self):
        assert service_from_flow(443, None, "TCP", "1.1.1.1", "2.2.2.2",
                                 website="www.google.com") == "Google"
        assert service_from_flow(443, None, "TCP", "1.1.1.1", "2.2.2.2") == "HTTPS/TLS"