"""Capture flow aggregation tests."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.capture.packet_capture import FlowKey, FlowTracker  # noqa: E402


def make_parsed(src, dst, sport, dport, proto="TCP", size=100, direction="outbound", encrypted=False, service="Unknown"):
    class P:
        pass

    p = P()
    p.source_ip = src
    p.destination_ip = dst
    p.source_port = sport
    p.destination_port = dport
    p.protocol = proto
    p.packet_size = size
    p.direction = direction
    p.encrypted = encrypted
    p.service = service
    return p


class TestFlowTracker:
    def test_grouping(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        tracker.process_parsed(make_parsed("192.168.1.10", "8.8.8.8", 1234, 443, direction="outbound", size=100))
        tracker.process_parsed(make_parsed("192.168.1.10", "8.8.8.8", 1234, 443, direction="outbound", size=200))
        tracker.process_parsed(make_parsed("192.168.1.10", "8.8.8.8", 1234, 443, direction="inbound", size=300))
        flows = tracker.active_flows()
        assert len(flows) == 1
        flow = flows[0]
        assert flow.bytes_sent == 300
        assert flow.bytes_received == 300
        assert flow.packets_sent == 2
        assert flow.packets_received == 1

    def test_timeout_closes_flow(self):
        closed = []
        tracker = FlowTracker(timeout_seconds=0.1, on_close=closed.append, local_ips={"192.168.1.10"})
        tracker.process_parsed(make_parsed("192.168.1.10", "8.8.8.8", 1111, 53, proto="UDP", direction="outbound"))
        time.sleep(0.15)
        tracker.close_stale()
        assert len(closed) == 1
        assert tracker.active_count() == 0

    def test_close_all_flushes(self):
        closed = []
        tracker = FlowTracker(timeout_seconds=60, on_close=closed.append, local_ips={"192.168.1.10"})
        tracker.process_parsed(make_parsed("192.168.1.10", "8.8.8.8", 2222, 443, direction="outbound"))
        tracker.close_all()
        assert len(closed) == 1
        assert closed[0].closed is True

    def test_direction_sets_device_ip(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        tracker.process_parsed(make_parsed("192.168.1.10", "8.8.8.8", 3333, 443, direction="outbound"))
        flow = tracker.active_flows()[0]
        assert flow.device_ip == "192.168.1.10"


class TestFlowKey:
    def test_key_equality(self):
        a = FlowKey("1.1.1.1", "2.2.2.2", 1, 2, "TCP")
        b = FlowKey("1.1.1.1", "2.2.2.2", 1, 2, "TCP")
        c = FlowKey("1.1.1.1", "2.2.2.2", 1, 3, "TCP")
        assert a == b
        assert a != c
        assert hash(a) == hash(b)