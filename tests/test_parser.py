"""Packet parser tests (pure-logic paths via synthetic packets where possible).

Scapy packet construction may require the capture interface; these tests use
constructed packet objects so they run without administrator privileges.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.capture.packet_parser import parse_packet  # noqa: E402


def make_ip_tcp(src, dst, sport, dport, flags=0x02, payload=b""):
    from scapy.layers.inet import IP, TCP
    from scapy.packet import Raw

    pkt = IP(src=src, dst=dst) / TCP(sport=sport, dport=dport, flags=flags)
    if payload:
        pkt = pkt / Raw(payload)
    return pkt


def make_ip_udp(src, dst, sport, dport):
    from scapy.layers.inet import IP, UDP

    return IP(src=src, dst=dst) / UDP(sport=sport, dport=dport)


class TestTcp:
    def test_https_flow_metadata(self):
        pkt = make_ip_tcp("192.168.1.10", "142.250.190.46", 52000, 443)
        parsed = parse_packet(pkt, local_ips={"192.168.1.10"})
        assert parsed is not None
        assert parsed.protocol == "TCP"
        assert parsed.destination_port == 443
        assert parsed.source_ip == "192.168.1.10"
        assert parsed.direction == "outbound"
        assert parsed.encrypted is True
        assert parsed.service == "HTTPS/TLS"

    def test_http_flow_metadata(self):
        pkt = make_ip_tcp("192.168.1.10", "192.168.1.1", 5000, 8000)
        parsed = parse_packet(pkt, local_ips={"192.168.1.10"})
        assert parsed is not None
        assert parsed.destination_port == 8000
        assert parsed.encrypted is False
        assert parsed.service == "HTTP"

    def test_packet_size_captured(self):
        pkt = make_ip_tcp("192.168.1.10", "1.1.1.1", 4000, 443, payload=b"\x16\x03\x01" + b"\x00" * 40)
        parsed = parse_packet(pkt, local_ips={"192.168.1.10"})
        assert parsed.packet_size == len(pkt)


class TestUdp:
    def test_dns_metadata(self):
        pkt = make_ip_udp("192.168.1.10", "8.8.8.8", 5353, 53)
        parsed = parse_packet(pkt, local_ips={"192.168.1.10"})
        assert parsed is not None
        assert parsed.protocol == "UDP"
        assert parsed.destination_port == 53
        assert parsed.service == "DNS"
        assert parsed.encrypted is False

    def test_inbound_direction(self):
        pkt = make_ip_udp("8.8.8.8", "192.168.1.10", 53, 5353)
        parsed = parse_packet(pkt, local_ips={"192.168.1.10"})
        assert parsed.direction == "inbound"


class TestOther:
    def test_no_ip_returns_none(self):
        from scapy.layers.l2 import Ether

        pkt = Ether()
        assert parse_packet(pkt) is None

    def test_unknown_protocol_label(self):
        from scapy.layers.inet import IP
        from scapy.packet import Raw

        pkt = IP(src="10.0.0.1", dst="10.0.0.2") / Raw(b"\x01" * 8)
        parsed = parse_packet(pkt, local_ips={"10.0.0.1"})
        assert parsed is not None
        assert parsed.protocol == "Other"