"""Metadata extraction tests: DNS responses and TLS SNI (metadata only)."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.capture.metadata_extractor import (  # noqa: E402
    extract_dns_metadata,
    extract_tls_sni,
)


def make_dns_response(qname, answer_ip, ttl=300, rrtype=1):
    from scapy.layers.dns import DNS, DNSQR, DNSRR
    from scapy.layers.inet import IP, UDP

    return (
        IP(src="8.8.8.8", dst="192.168.1.10")
        / UDP(sport=53, dport=5353)
        / DNS(id=1, qr=1, qd=DNSQR(qname=qname, qtype=rrtype),
              an=DNSRR(rrname=qname, type=rrtype, ttl=ttl, rdata=answer_ip))
    )


def make_dns_query(qname):
    from scapy.layers.dns import DNS, DNSQR
    from scapy.layers.inet import IP, UDP

    return (
        IP(src="192.168.1.10", dst="8.8.8.8")
        / UDP(sport=5353, dport=53)
        / DNS(id=2, qd=DNSQR(qname=qname, qtype=1))
    )


def make_tls_client_hello(sni):
    from scapy.layers.tls.extensions import ServerName, TLS_Ext_ServerName

    ext_bytes = b""
    if sni:
        ext_bytes = bytes(TLS_Ext_ServerName(servernames=[ServerName(nametype=0, servername=sni)]))
    ciphers = b"\x13\x01\x13\x02"
    body = (
        b"\x03\x03" + b"\x00" * 32 + b"\x00"
        + struct.pack(">H", len(ciphers)) + ciphers
        + b"\x01\x00" + struct.pack(">H", len(ext_bytes)) + ext_bytes
    )
    hs = b"\x01" + struct.pack(">I", len(body))[1:] + body
    return b"\x16\x03\x01" + struct.pack(">H", len(hs)) + hs


def make_tcp_with_payload(payload, dport=443):
    from scapy.layers.inet import IP, TCP
    from scapy.packet import Raw

    return IP(src="192.168.1.10", dst="140.82.121.4") / TCP(sport=50000, dport=dport, flags=0x02) / Raw(payload)


class TestDnsMetadata:
    def test_a_response_recorded(self):
        pkt = make_dns_response("www.google.com.", "142.250.190.46")
        results = extract_dns_metadata(pkt)
        assert ("142.250.190.46", "www.google.com", 300) in results

    def test_query_ignored(self):
        pkt = make_dns_query("www.google.com.")
        assert extract_dns_metadata(pkt) == []

    def test_aaaa_response_recorded(self):
        pkt = make_dns_response("ipv6.google.com.", "2607:f8b0:4005:805::200e", rrtype=28)
        results = extract_dns_metadata(pkt)
        assert len(results) == 1
        ip, domain, _ = results[0]
        assert ":" in ip
        assert domain == "ipv6.google.com"

    def test_non_dns_ignored(self):
        from scapy.layers.inet import IP, TCP

        pkt = IP(src="1.1.1.1", dst="2.2.2.2") / TCP(sport=1, dport=2)
        assert extract_dns_metadata(pkt) == []


class TestTlsSni:
    def test_sni_extracted(self):
        pkt = make_tcp_with_payload(make_tls_client_hello(b"github.com"))
        assert extract_tls_sni(pkt) == "github.com"

    def test_no_sni_returns_none(self):
        pkt = make_tcp_with_payload(make_tls_client_hello(None))
        assert extract_tls_sni(pkt) is None

    def test_application_data_ignored(self):
        pkt = make_tcp_with_payload(b"\x17\x03\x01" + b"\x00" * 20)
        assert extract_tls_sni(pkt) is None

    def test_udp_ignored(self):
        from scapy.layers.inet import IP, UDP

        pkt = IP(src="1.1.1.1", dst="2.2.2.2") / UDP(sport=1, dport=2)
        assert extract_tls_sni(pkt) is None

    def test_fragmented_record_skipped(self):
        from scapy.layers.tls.extensions import ServerName, TLS_Ext_ServerName

        sni = b"example.com"
        ext_bytes = bytes(TLS_Ext_ServerName(servernames=[ServerName(nametype=0, servername=sni)]))
        ciphers = b"\x13\x01\x13\x02"
        body = (
            b"\x03\x03" + b"\x00" * 32 + b"\x00"
            + struct.pack(">H", len(ciphers)) + ciphers
            + b"\x01\x00" + struct.pack(">H", len(ext_bytes)) + ext_bytes
        )
        hs = b"\x01" + struct.pack(">I", len(body))[1:] + body
        record = b"\x16\x03\x01" + struct.pack(">H", len(hs)) + hs
        truncated = record[:12]  # record length exceeds available bytes
        pkt = make_tcp_with_payload(truncated)
        assert extract_tls_sni(pkt) is None