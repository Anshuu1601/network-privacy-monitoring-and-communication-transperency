"""Protocol identification from ports and observable protocol information.

Port-based identification alone is not proof of encryption; labels are
reported as observed metadata only. Never inspects decrypted content.
"""
from dataclasses import dataclass
from typing import Optional

from scapy.layers.inet import TCP
from scapy.packet import Packet, Raw

KNOWN_PORTS = {
    20: ("FTP Data", "TCP", False),
    21: ("FTP", "TCP", False),
    22: ("SSH", "TCP", True),
    23: ("Telnet", "TCP", False),
    25: ("SMTP", "TCP", False),
    53: ("DNS", "UDP", False),
    67: ("DHCP", "UDP", False),
    68: ("DHCP", "UDP", False),
    80: ("HTTP", "TCP", False),
    110: ("POP3", "TCP", False),
    123: ("NTP", "UDP", False),
    143: ("IMAP", "TCP", False),
    443: ("HTTPS/TLS", "TCP", True),
    465: ("SMTPS", "TCP", True),
    587: ("SMTP", "TCP", False),
    853: ("DNS-over-TLS", "TCP", True),
    993: ("IMAPS", "TCP", True),
    995: ("POP3S", "TCP", True),
    1080: ("SOCKS Proxy", "TCP", False),
    3306: ("MySQL", "TCP", False),
    5432: ("PostgreSQL", "TCP", False),
    6379: ("Redis", "TCP", False),
    8000: ("HTTP", "TCP", False),
    8080: ("HTTP", "TCP", False),
    8888: ("HTTP", "TCP", False),
    9000: ("HTTP", "TCP", False),
}

_TLS_RECORD_HEADER = b"\x16\x03"


@dataclass
class ProtocolInfo:
    protocol: str
    service: str
    encrypted: bool
    confidence: str


def identify_protocol(ip_protocol: str, src_port: Optional[int], dst_port: Optional[int],
                      pkt: Optional[Packet] = None) -> ProtocolInfo:
    """Return ProtocolInfo for a packet. Uses port mappings and, where safe,
    observable transport metadata. Never inspects application content."""
    port = dst_port or src_port
    entry = KNOWN_PORTS.get(port)
    if entry:
        service, proto, encrypted = entry
    else:
        service, proto, encrypted = "Unknown", ip_protocol or "Other", False

    protocol = ip_protocol or "Other"
    confidence = "port" if entry else "none"

    if protocol == "TCP" and service == "Unknown" and pkt is not None:
        try:
            if TCP in pkt and Raw in pkt:
                payload = bytes(pkt[Raw])
                if len(payload) > 5 and payload[:3] == _TLS_RECORD_HEADER:
                    encrypted = True
                    confidence = "tls-record"
                    service = "HTTPS/TLS"
        except Exception:
            pass

    return ProtocolInfo(protocol=protocol, service=service, encrypted=bool(encrypted),
                        confidence=confidence)