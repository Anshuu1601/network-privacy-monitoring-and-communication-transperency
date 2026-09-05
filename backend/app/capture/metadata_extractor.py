"""Best-effort, metadata-only extraction of DNS mappings and TLS SNI.

Nothing here decrypts or inspects content: DNS response records and the SNI
extension of a TLS ClientHello are observable metadata already on the wire.
"""
import ipaddress
import logging

from scapy.layers.dns import DNS, DNSRR
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.inet6 import IPv6

logger = logging.getLogger("privacy.metadata")

_KNOWN_RR = {1: "A", 28: "AAAA"}


def _decode_qname(qname) -> str:
    if isinstance(qname, bytes):
        try:
            return qname.decode("utf-8", "replace").rstrip(".")
        except Exception:
            return ""
    return str(qname).rstrip(".")


def _ip_from_rdata(rdata, rrtype) -> str | None:
    try:
        if rrtype == 1:  # A
            if isinstance(rdata, str):
                return str(ipaddress.IPv4Address(rdata))
            return str(ipaddress.IPv4Address(bytes(rdata)[:4]))
        if rrtype == 28:  # AAAA
            if isinstance(rdata, str):
                return str(ipaddress.IPv6Address(rdata))
            return str(ipaddress.IPv6Address(bytes(rdata)[:16]))
    except Exception:
        return None
    return None


def extract_dns_metadata(pkt) -> list[tuple]:
    """Return [(ip, domain, ttl), ...] recorded by a DNS *response* packet.

    Only answers of type A and AAAA are considered; queries are ignored.
    """
    if DNS not in pkt:
        return []
    dns = pkt[DNS]
    try:
        if int(dns.qr) != 1:
            return []
    except (TypeError, ValueError):
        return []

    results = []
    answers = dns.an
    if isinstance(answers, DNSRR):
        answers = [answers]
    elif not isinstance(answers, (list, tuple)):
        try:
            answers = list(answers)
        except TypeError:
            answers = []
    for rr in answers:
        if not isinstance(rr, DNSRR):
            continue
        rrtype = int(rr.type)
        if rrtype not in _KNOWN_RR:
            continue
        ip = _ip_from_rdata(rr.rdata, rrtype)
        domain = _decode_qname(rr.rrname)
        if ip and domain:
            try:
                ttl = int(rr.ttl)
            except (TypeError, ValueError):
                ttl = None
            results.append((ip, domain, ttl))
    return results


def extract_tls_sni(pkt) -> str | None:
    """Return the SNI hostname from a TLS ClientHello, or None.

    Only the first handshake record of a TCP segment is inspected and only
    when it fits entirely in the segment (best effort; split records skipped).
    """
    if TCP not in pkt:
        return None
    try:
        from scapy.packet import Raw

        if Raw not in pkt:
            return None
        payload = bytes(pkt[Raw])
        if len(payload) < 6 or payload[0] != 0x16:  # handshake record type
            return None
        record_len = int.from_bytes(payload[3:5], "big")
        if record_len + 5 > len(payload):
            return None  # fragmented ClientHello — skip (best effort)
        handshake = payload[5:]
        if handshake[0] != 0x01:  # client_hello handshake type
            return None

        from scapy.layers.tls.handshake import TLSClientHello

        hello = TLSClientHello(handshake)
        for ext in getattr(hello, "ext", None) or []:
            if int(ext.type) == 0:  # server_name extension
                names = [sn.servername for sn in ext.servernames]
                if names:
                    hostname = _decode_qname(names[0])
                    if hostname:
                        return hostname
    except Exception:
        logger.debug("TLS SNI extraction skipped", exc_info=True)
    return None