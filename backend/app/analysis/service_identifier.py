"""Service identification from flow metadata (ports, and DNS names when safe).

Only observable metadata is used. No invasive traffic inspection.
"""
import ipaddress

from app.analysis.protocol_analyzer import KNOWN_PORTS

# Domain suffix → friendly service label. Only well-known, stable providers are
# listed so the dashboard never fabricates a name.
DOMAIN_SERVICES = {
    "google.com": "Google",
    "youtube.com": "YouTube",
    "googleapis.com": "Google",
    "gstatic.com": "Google",
    "github.com": "GitHub",
    "githubusercontent.com": "GitHub",
    "microsoft.com": "Microsoft",
    "live.com": "Microsoft",
    "office.com": "Microsoft",
    "outlook.com": "Microsoft",
    "azure.com": "Microsoft Azure",
    "cloudflare.com": "Cloudflare",
    "amazon.com": "Amazon",
    "aws.amazon.com": "AWS",
    "netflix.com": "Netflix",
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "meta.com": "Meta",
    "twitter.com": "Twitter",
    "x.com": "X",
    "whatsapp.com": "WhatsApp",
    "telegram.org": "Telegram",
    "apple.com": "Apple",
    "icloud.com": "Apple",
    "spotify.com": "Spotify",
    "reddit.com": "Reddit",
    "linkedin.com": "LinkedIn",
    "mozilla.org": "Mozilla",
    "wikipedia.org": "Wikipedia",
    "duckduckgo.com": "DuckDuckGo",
    "bing.com": "Bing",
    "yahoo.com": "Yahoo",
    "dropbox.com": "Dropbox",
    "slack.com": "Slack",
    "zoom.us": "Zoom",
    "twitch.tv": "Twitch",
    "discord.com": "Discord",
    "openai.com": "OpenAI",
    "anthropic.com": "Anthropic",
    "stackoverflow.com": "Stack Overflow",
    "wordpress.com": "WordPress",
    "shopify.com": "Shopify",
    "paypal.com": "PayPal",
    "stripe.com": "Stripe",
    "cloudflare-dns.com": "Cloudflare",
    "digicert.com": "DigiCert",
}

# Registered domains with a two-level public suffix (heuristic eTLD+1).
_TWO_PART_TLDS = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "me.uk", "com.au", "net.au", "org.au",
    "co.jp", "co.in", "com.br", "com.mx", "co.nz", "com.sg", "co.za", "com.cn",
    "com.tr", "co.kr", "com.hk", "com.ar", "com.pe", "com.eg", "com.ua",
}


def extract_registered_domain(hostname: str) -> str:
    """Return the registrable domain (eTLD+1 heuristic) for a hostname.

    Unknown/empty values and raw IP addresses are returned unchanged.
    """
    if not hostname or hostname == "Unknown":
        return hostname
    hostname = hostname.strip().rstrip(".").lower()
    try:
        ipaddress.ip_address(hostname)
        return hostname
    except ValueError:
        pass
    parts = hostname.split(".")
    if len(parts) <= 2:
        return hostname
    if ".".join(parts[-2:]) in _TWO_PART_TLDS:
        return ".".join(parts[-3:]) if len(parts) >= 3 else hostname
    return ".".join(parts[-2:])


def service_from_domain(domain: str) -> str | None:
    """Friendly service label for a domain, or None when not recognized."""
    if not domain or domain == "Unknown":
        return None
    d = domain.strip().lower()
    for suffix, service in DOMAIN_SERVICES.items():
        if d == suffix or d.endswith("." + suffix):
            return service
    return None


def domain_for_service(service: str) -> str | None:
    """Reverse lookup: known service label → representative domain."""
    if not service:
        return None
    return {v: k for k, v in DOMAIN_SERVICES.items()}.get(service)


def service_from_flow(dst_port, src_port, protocol, destination_ip, source_ip,
                      website: str | None = None) -> str:
    """Identify a service: friendly label when a known website is available,
    otherwise port-based protocol/service."""
    if website and website != "Unknown":
        svc = service_from_domain(website)
        if svc:
            return svc
    port = dst_port or src_port
    entry = KNOWN_PORTS.get(port)
    if entry:
        return entry[0]
    return "Unknown"


def normalize_service(raw: str) -> str:
    if not raw or raw == "Unknown":
        return "Other"
    return raw


def top_service_buckets(service_counts: list[dict], max_buckets: int = 5) -> list[dict]:
    """Bucket a list of {service, bytes, count} into top-N + 'Other'."""
    ranked = sorted(service_counts, key=lambda r: r.get("bytes", 0) or 0, reverse=True)
    top = ranked[:max_buckets]
    rest = ranked[max_buckets:]
    others_bytes = sum(r.get("bytes", 0) or 0 for r in rest)
    others_count = sum(r.get("count", 0) or 0 for r in rest)
    buckets = [{"service": r["service"], "bytes": r.get("bytes", 0), "count": r.get("count", 0)}
               for r in top]
    if rest:
        buckets.append({"service": "Other", "bytes": others_bytes, "count": others_count})
    return buckets