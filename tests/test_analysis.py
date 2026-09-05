"""Analysis module tests: traffic analyzer, protocol/service/encryption."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.analysis.encryption_analyzer import encryption_label  # noqa: E402
from app.analysis.protocol_analyzer import identify_protocol  # noqa: E402
from app.analysis.service_identifier import service_from_flow, top_service_buckets  # noqa: E402
from app.analysis.traffic_analyzer import compute_throughput, sum_bytes  # noqa: E402
from app.capture.packet_capture import Flow  # noqa: E402


def make_flow(sent=0, received=0, last_seen=None):
    return Flow(
        key=None,
        start_time=time.time(),
        last_seen=last_seen or time.time(),
        bytes_sent=sent,
        bytes_received=received,
    )


class TestTrafficAnalyzer:
    def test_upload_download_totals(self):
        flows = [make_flow(sent=1000, received=500), make_flow(sent=2000, received=2500)]
        totals = sum_bytes(flows)
        assert totals["bytes_sent"] == 3000
        assert totals["bytes_received"] == 3000
        assert totals["total"] == 6000

    def test_throughput_window(self):
        now = time.time()
        old = make_flow(sent=100_000, last_seen=now - 60)
        recent = make_flow(sent=10_000, received=20_000, last_seen=now)
        speed = compute_throughput([old, recent], window_seconds=10)
        assert speed["upload_bps"] == 1000.0
        assert speed["download_bps"] == 2000.0


class TestProtocolAnalyzer:
    def test_http_port(self):
        info = identify_protocol("TCP", 50000, 80, None)
        assert info.service == "HTTP"
        assert info.encrypted is False

    def test_https_port(self):
        info = identify_protocol("TCP", 50000, 443, None)
        assert info.service == "HTTPS/TLS"
        assert info.encrypted is True

    def test_ssh_port(self):
        info = identify_protocol("TCP", 12345, 22, None)
        assert info.service == "SSH"
        assert info.encrypted is True

    def test_dns_port(self):
        info = identify_protocol("UDP", 5353, 53, None)
        assert info.service == "DNS"
        assert info.encrypted is False

    def test_unknown_port(self):
        info = identify_protocol("TCP", 40000, 9999, None)
        assert info.service == "Unknown"
        assert info.encrypted is False


class TestServiceIdentifier:
    def test_known_ports(self):
        assert service_from_flow(443, None, "TCP", "1.1.1.1", "2.2.2.2") == "HTTPS/TLS"
        assert service_from_flow(80, None, "TCP", "1.1.1.1", "2.2.2.2") == "HTTP"
        assert service_from_flow(53, None, "UDP", "8.8.8.8", "2.2.2.2") == "DNS"

    def test_unknown(self):
        assert service_from_flow(12345, None, "TCP", "1.1.1.1", "2.2.2.2") == "Unknown"

    def test_top_buckets(self):
        counts = [
            {"service": "Google", "bytes": 1000, "count": 5},
            {"service": "YouTube", "bytes": 900, "count": 4},
            {"service": "Microsoft", "bytes": 800, "count": 3},
            {"service": "DNS", "bytes": 700, "count": 20},
            {"service": "HTTP", "bytes": 600, "count": 2},
            {"service": "Other2", "bytes": 100, "count": 1},
        ]
        buckets = top_service_buckets(counts, max_buckets=5)
        assert buckets[-1]["service"] == "Other"
        assert buckets[-1]["bytes"] == 100


class TestEncryptionAnalyzer:
    def test_labels(self):
        assert encryption_label(True) == "Encryption detected"
        assert encryption_label(False, "HTTP") == "Encryption not detected"
        assert encryption_label(False, "TCP") == "Encryption not detected"