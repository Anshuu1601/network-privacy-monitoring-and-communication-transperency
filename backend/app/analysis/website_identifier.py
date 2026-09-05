"""Website/domain resolution from observable metadata.

Privacy-preserving priority chain (never fabricates names):
  1. Reliable TLS SNI hostname
  2. Recent DNS mapping (expiring)
  3. Known service/domain information
  4. Destination IP
  5. Unknown

Applications are intentionally left "Unknown" unless reliably identifiable —
no application is ever guessed from a domain or port.
"""
from app.analysis.service_identifier import extract_registered_domain, service_from_domain

UNKNOWN_LEVEL = 0
IP_LEVEL = 1
SERVICE_LEVEL = 2
DNS_LEVEL = 3
SNI_LEVEL = 4


def _source_level(parsed, dns_cache) -> int:
    if getattr(parsed, "sni", None):
        return SNI_LEVEL
    if dns_cache and getattr(parsed, "destination_ip", None) and dns_cache.lookup(parsed.destination_ip):
        return DNS_LEVEL
    if getattr(parsed, "destination_ip", None):
        return IP_LEVEL
    return UNKNOWN_LEVEL


def resolve_website(parsed, dns_cache) -> str:
    """Resolve a website label for a parsed packet using the priority chain."""
    sni = getattr(parsed, "sni", None)
    if sni:
        return sni
    dst = getattr(parsed, "destination_ip", None)
    if dns_cache and dst:
        name = dns_cache.lookup(dst)
        if name:
            return name
    if dst:
        return dst
    return "Unknown"


def resolve_website_level(parsed, dns_cache) -> int:
    return _source_level(parsed, dns_cache)


def apply_website_to_flow(flow, parsed, dns_cache) -> str:
    """Upgrade a flow's website/domain only when the new signal is more
    reliable than what is already known."""
    level = resolve_website_level(parsed, dns_cache)
    if level > flow.website_level:
        website = resolve_website(parsed, dns_cache)
        flow.website = website
        flow.website_level = level
        flow.domain = extract_registered_domain(website)
    return flow.website