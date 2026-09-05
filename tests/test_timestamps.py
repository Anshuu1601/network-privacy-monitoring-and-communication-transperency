"""Timestamp / timezone / flow-timing tests.

Covers: packet timestamp preservation, UTC serialization, distinct per-flow
timestamps, start_time / last_seen / duration (including active flows), demo
timestamp progression, API timestamp format, and reports timezone labeling.

The frontend converts the UTC instant to the browser's local timezone exactly
once; tests here verify the backend never emits ambiguous (timezone-less) ISO
strings and that the UTC instant is preserved end-to-end.
"""
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.capture.packet_capture import FlowTracker, demo_event_time  # noqa: E402
from app.capture.packet_parser import parse_packet  # noqa: E402
from app.timeutils import from_unix, to_iso_utc, to_naive_utc, utc_now_iso  # noqa: E402

UTC = timezone.utc
REF_INSTANT = datetime(2026, 8, 19, 17, 31, 41, 123000, tzinfo=UTC)


def make_parsed(src="192.168.1.10", dst="8.8.8.8", sport=4000, dport=443,
                proto="TCP", size=100, direction="outbound", ts=None):
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
    p.encrypted = dport in (443, 22, 853)
    p.service = "HTTPS/TLS"
    p.sni = None
    p.timestamp = ts if ts is not None else from_unix(time.time())
    return p


class TestTimeutils:
    def test_iso_serialization_uses_z(self):
        assert to_iso_utc(REF_INSTANT) == "2026-08-19T17:31:41.123Z"

    def test_naive_datetime_assumed_utc(self):
        naive = REF_INSTANT.replace(tzinfo=None)
        assert to_iso_utc(naive) == "2026-08-19T17:31:41.123Z"

    def test_aware_other_offset_normalized_to_utc(self):
        shifted = REF_INSTANT.astimezone(timezone(timedelta(hours=6)))
        assert to_iso_utc(shifted) == "2026-08-19T17:31:41.123Z"

    def test_roundtrip_same_instant(self):
        iso = to_iso_utc(REF_INSTANT)
        parsed = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        assert parsed == REF_INSTANT

    def test_to_naive_utc_drops_offset(self):
        naive = to_naive_utc(REF_INSTANT)
        assert naive.tzinfo is None
        assert naive == REF_INSTANT.replace(tzinfo=None)

    def test_from_unix_preserves_instant(self):
        epoch = REF_INSTANT.timestamp()
        assert from_unix(epoch) == REF_INSTANT

    def test_utc_now_iso_is_utc(self):
        iso = utc_now_iso()
        assert iso.endswith("Z")
        parsed = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None
        assert abs((parsed - datetime.now(UTC)).total_seconds()) < 60

    def test_empty_value_serializes_to_none(self):
        assert to_iso_utc(None) is None


class TestPacketTimestampPreservation:
    def test_scapy_packet_time_used(self):
        from scapy.layers.inet import IP, TCP

        epoch = REF_INSTANT.timestamp()
        pkt = IP(src="192.168.1.10", dst="8.8.8.8") / TCP(sport=4000, dport=443)
        pkt.time = epoch
        parsed = parse_packet(pkt, local_ips={"192.168.1.10"})
        assert parsed is not None
        assert parsed.timestamp.tzinfo is not None
        assert parsed.timestamp == REF_INSTANT

    def test_timestamp_survives_to_dict_as_utc(self):
        from scapy.layers.inet import IP, TCP

        pkt = IP(src="192.168.1.10", dst="8.8.8.8") / TCP(sport=4000, dport=443)
        pkt.time = REF_INSTANT.timestamp()
        parsed = parse_packet(pkt, local_ips={"192.168.1.10"})
        assert parsed.to_dict()["timestamp"] == "2026-08-19T17:31:41.123Z"

    def test_missing_packet_time_falls_back(self):
        from scapy.layers.inet import IP, TCP

        pkt = IP(src="192.168.1.10", dst="8.8.8.8") / TCP(sport=4000, dport=443)
        pkt.time = 0.0  # constructed packet without a real capture time
        parsed = parse_packet(pkt, local_ips={"192.168.1.10"})
        assert parsed is not None
        assert abs((parsed.timestamp - datetime.now(UTC)).total_seconds()) < 60


class TestFlowTiming:
    def test_distinct_flows_get_distinct_timestamps(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        t1 = from_unix(time.time() - 30)
        t2 = from_unix(time.time() - 20)
        flow_a, _ = tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4001, ts=t1))
        flow_b, _ = tracker.process_parsed(make_parsed(dst="2.2.2.2", sport=4002, ts=t2))
        assert flow_a.first_seen == t1
        assert flow_b.first_seen == t2
        assert flow_a.first_seen != flow_b.first_seen

    def test_start_time_is_first_packet_time(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        t1 = from_unix(time.time() - 10)
        t2 = t1 + timedelta(seconds=4)
        flow, _ = tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4101, ts=t1))
        tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4101, ts=t2))
        assert flow.start_time == t1.timestamp()
        assert flow.first_seen == t1

    def test_last_seen_is_latest_packet_time(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        t1 = from_unix(time.time() - 10)
        t2 = t1 + timedelta(seconds=4)
        flow, _ = tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4102, ts=t1))
        tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4102, ts=t2))
        assert flow.last_seen == t2.timestamp()
        assert flow.last_seen_dt == t2

    def test_duration_is_last_minus_first(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        t1 = from_unix(time.time() - 20)
        t2 = t1 + timedelta(seconds=8)
        flow, _ = tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4103, ts=t1))
        tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4103, ts=t2))
        assert flow.duration() == pytest.approx(8.0, abs=0.001)

    def test_active_duration_updates(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        t1 = from_unix(time.time() - 5)
        flow, _ = tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4104, ts=t1))
        d1 = flow.duration()
        tracker.process_parsed(make_parsed(dst="1.1.1.1", sport=4104, ts=t1 + timedelta(seconds=2)))
        d2 = flow.duration()
        assert d2 > d1
        assert d1 == pytest.approx(0.0, abs=0.001)
        assert d2 == pytest.approx(2.0, abs=0.001)


class TestDemoTimestampProgression:
    def test_demo_events_progress_within_tick(self):
        now = time.time()
        times = [demo_event_time(now, i, jitter=0) for i in range(5)]
        assert len(set(times)) == 5
        for a, b in zip(times, times[1:]):
            assert b > a
            assert (b - a).total_seconds() > 0.2
        assert all(t.tzinfo is not None for t in times)

    def test_demo_events_stay_near_wall_clock(self):
        now = time.time()
        t = demo_event_time(now, 0)
        assert abs(t.timestamp() - now) < 1.0

    def test_flow_tracker_with_demo_times(self):
        tracker = FlowTracker(timeout_seconds=60, local_ips={"192.168.1.10"})
        now = time.time()
        flows = []
        for i in range(4):
            ts = demo_event_time(now, i, jitter=0)
            flow, _ = tracker.process_parsed(
                make_parsed(dst=f"10.0.0.{i + 1}", sport=5000 + i, ts=ts)
            )
            flows.append(flow)
        stamps = [f.first_seen for f in flows]
        assert len(set(stamps)) == 4


class TestApiTimestampFormat:
    def test_history_returns_utc_iso(self):
        from app.database.database import init_db, SessionLocal
        from app.main import app
        from fastapi.testclient import TestClient

        init_db()
        with TestClient(app) as client:
            resp = client.get("/api/traffic/history?limit=5")
            assert resp.status_code == 200
            rows = resp.json()
            for row in rows:
                if row.get("timestamp"):
                    assert row["timestamp"].endswith("Z")
                    datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))

    def test_alert_timestamps_are_utc(self):
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/api/alerts?limit=10")
            assert resp.status_code == 200
            for alert in resp.json():
                if alert.get("timestamp"):
                    assert alert["timestamp"].endswith("Z")

    def test_report_states_timezone_and_utc_times(self):
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/api/reports/daily")
            assert resp.status_code == 200
            body = resp.json()
            assert body["timezone"] == "UTC"
            assert body["start_time"].endswith("Z")
            assert body["end_time"].endswith("Z")
            for alert in body.get("alerts", []):
                if alert.get("timestamp"):
                    assert alert["timestamp"].endswith("Z")

    def test_live_timestamps_are_utc(self):
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/api/traffic/live")
            assert resp.status_code == 200
            body = resp.json()
            assert body["timestamp"].endswith("Z")
            for conn in body.get("active_connections", []):
                if conn.get("timestamp"):
                    assert conn["timestamp"].endswith("Z")


if __name__ == "__main__":  # pragma: no cover
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))