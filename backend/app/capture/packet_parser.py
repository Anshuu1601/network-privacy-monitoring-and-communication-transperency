"""Packet parsing: convert raw Scapy packets into normalized metadata records.

Only metadata is extracted. No payloads, bodies, cookies, messages or tokens
are ever stored or transmitted.
"""
import time
from datetime import datetime, timezone

from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import Ether
from scapy.packet import Packet

from app.analysis.protocol_analyzer import ProtocolInfo, identify_protocol
from app.timeutils import to_iso_utc


def now_iso() -> str:
    return to_iso_utc(datetime.now(timezone.utc))


def packet_time(pkt: Packet) -> datetime:
    """The actual capture time of a Scapy packet as an aware UTC datetime.

    Scapy stamps every sniffed packet with ``pkt.time`` (Unix epoch seconds).
    Constructed packets may carry a missing/zero time, so fall back to the
    processing time rather than producing a 1970-01-01 timestamp.
    """
    try:
        ts = float(getattr(pkt, "time", 0) or 0)
    except (TypeError, ValueError):
        ts = 0.0
    if ts <= 0:
        ts = time.time()
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _extract_ports(protocol: str, pkt: Packet):
    src_port = None
    dst_port = None
    if protocol in ("TCP", "UDP"):
        layer = pkt[TCP] if protocol == "TCP" else pkt[UDP]
        src_port = int(layer.sport)
        dst_port = int(layer.dport)
    return src_port, dst_port


def _determine_direction(pkt: Packet, local_ips: set[str]) -> str:
    if IP in pkt:
        src = pkt[IP].src
        dst = pkt[IP].dst
    elif IPv6 in pkt:
        src = pkt[IPv6].src
        dst = pkt[IPv6].dst
    else:
        return "unknown"
    if src in local_ips:
        return "outbound"
    if dst in local_ips:
        return "inbound"
    return "unknown"


class ParsedPacket:
    __slots__ = (
        "timestamp",
        "source_ip",
        "destination_ip",
        "source_port",
        "destination_port",
        "protocol",
        "packet_size",
        "direction",
        "interface",
        "encrypted",
        "service",
        "tcp_flags",
        "raw_protocol",
        "sni",
    )

    def to_dict(self) -> dict:
        return {
            "timestamp": to_iso_utc(self.timestamp),
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "protocol": self.protocol,
            "packet_size": self.packet_size,
            "direction": self.direction,
            "interface": self.interface,
            "encrypted": self.encrypted,
            "service": self.service,
        }


def parse_packet(pkt: Packet, interface: str = "", local_ips: set[str] | None = None) -> ParsedPacket | None:
    """Parse a single packet into normalized metadata. Returns None if the
    packet has no IP layer (e.g. ARP broadcast that carries no traffic flow)."""
    local_ips = local_ips or set()

    if IP in pkt:
        ip_layer = pkt[IP]
        source_ip = ip_layer.src
        destination_ip = ip_layer.dst
        protocol = "TCP" if TCP in pkt else ("UDP" if UDP in pkt else ("ICMP" if ICMP in pkt else "Other"))
    elif IPv6 in pkt:
        ip_layer = pkt[IPv6]
        source_ip = ip_layer.src
        destination_ip = ip_layer.dst
        protocol = "TCP" if TCP in pkt else ("UDP" if UDP in pkt else ("ICMP" if ICMP in pkt else "Other"))
    else:
        return None

    src_port, dst_port = _extract_ports(protocol, pkt)
    packet_size = len(pkt)
    direction = _determine_direction(pkt, local_ips)

    proto_info = identify_protocol(protocol, src_port, dst_port, pkt)
    parsed = ParsedPacket()
    parsed.timestamp = packet_time(pkt)
    parsed.source_ip = source_ip
    parsed.destination_ip = destination_ip
    parsed.source_port = src_port
    parsed.destination_port = dst_port
    parsed.protocol = proto_info.protocol
    parsed.packet_size = packet_size
    parsed.direction = direction
    parsed.interface = interface
    parsed.encrypted = proto_info.encrypted
    parsed.service = proto_info.service
    parsed.raw_protocol = protocol
    parsed.tcp_flags = int(pkt[TCP].flags) if TCP in pkt else 0
    parsed.sni = None
    return parsed


def build_local_ip_set(pkt: Packet) -> set[str]:
    """Heuristic: for a single-device demo, treat the device's own address
    as local so direction can be assigned. Full multi-device support uses the
    interface's configured addresses instead."""
    ips = set()
    if IP in pkt:
        if getattr(pkt[IP], "src", None):
            ips.add(pkt[IP].src)
    if IPv6 in pkt:
        if getattr(pkt[IPv6], "src", None):
            ips.add(pkt[IPv6].src)
    return ips