"""Packet capture and flow aggregation.

Runs Scapy sniffing in a background thread so FastAPI request handling is
never blocked. Packets are grouped into *flows* (one row per connection) so
thousands of packets become a handful of database records.

Only metadata is captured. Payloads are never stored.
"""
import ipaddress
import logging
import socket
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from scapy.all import AsyncSniffer, conf, get_if_list
from scapy.interfaces import NetworkInterface

from app.analysis.encryption_analyzer import encryption_label
from app.analysis.dns_cache import DnsCache
from app.analysis.service_identifier import service_from_domain, service_from_flow
from app.analysis.website_identifier import apply_website_to_flow
from app.capture.metadata_extractor import extract_dns_metadata, extract_tls_sni
from app.capture.packet_parser import build_local_ip_set, parse_packet
from app.config import settings
from app.timeutils import utc_now_naive

logger = logging.getLogger("privacy.capture")

MIN_IP = ipaddress.ip_address("100.64.0.0")
MAX_IP = ipaddress.ip_address("100.127.255.255")
WELL_KNOWN_RANGES = (ipaddress.ip_address("0.0.0.0"), ipaddress.ip_address("255.255.255.255"))


def demo_event_time(now: float, index: int, spread: float = 0.25, jitter: float = 0.08) -> datetime:
    """Synthetic capture time for the index-th demo event of a tick.

    Each event in a tick gets a distinct, increasing capture time so demo
    flows never share an identical timestamp and progress realistically.
    Returns an aware UTC datetime derived from the synthetic schedule.
    """
    import random

    from app.timeutils import from_unix

    return from_unix(now + index * spread + random.uniform(0, jitter))


def is_private_or_loopback(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback
    except ValueError:
        return False


@dataclass(frozen=True)
class FlowKey:
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str


@dataclass
class Flow:
    key: FlowKey
    start_time: float
    last_seen: float
    bytes_sent: int = 0
    bytes_received: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    service: str = "Unknown"
    encrypted: bool = False
    device_ip: str = ""
    closed: bool = False
    first_seen: datetime = field(default_factory=utc_now_naive)
    last_seen_dt: datetime = field(default_factory=utc_now_naive)
    website: str = "Unknown"
    domain: str = "Unknown"
    application: str = "Unknown"
    website_level: int = 0

    def duration(self) -> float:
        return max(0.0, self.last_seen - self.start_time)


class FlowTracker:
    def __init__(self, timeout_seconds: float = 60.0, on_close=None, local_ips: set[str] | None = None,
                 dns_cache=None):
        self.timeout = timeout_seconds
        self.on_close = on_close
        self.local_ips = local_ips or set()
        self.dns_cache = dns_cache
        self._flows: dict[FlowKey, Flow] = {}
        self._lock = threading.Lock()

    def set_local_ips(self, ips: set[str]):
        self.local_ips = ips

    def _flow_direction(self, flow: Flow) -> str:
        if flow.key.source_ip in self.local_ips:
            return "outbound"
        if flow.key.destination_ip in self.local_ips:
            return "inbound"
        return "unknown"

    def process_parsed(self, parsed) -> tuple[Flow, bool]:
        key = FlowKey(
            source_ip=parsed.source_ip,
            destination_ip=parsed.destination_ip,
            source_port=parsed.source_port,
            destination_port=parsed.destination_port,
            protocol=parsed.protocol,
        )
        pkt_ts = getattr(parsed, "timestamp", None)
        if pkt_ts is None:
            pkt_ts = datetime.now(timezone.utc)
        elif pkt_ts.tzinfo is None:
            pkt_ts = pkt_ts.replace(tzinfo=timezone.utc)
        else:
            pkt_ts = pkt_ts.astimezone(timezone.utc)
        ts_epoch = pkt_ts.timestamp()
        is_new = False
        with self._lock:
            flow = self._flows.get(key)
            if flow is None:
                is_new = True
                flow = Flow(key=key, start_time=ts_epoch, last_seen=ts_epoch)
                flow.first_seen = pkt_ts
                flow.last_seen_dt = pkt_ts
                flow.service = service_from_flow(
                    key.destination_port, key.source_port, key.protocol,
                    key.destination_ip, key.source_ip,
                )
                flow.encrypted = parsed.encrypted or key.destination_port in (443, 22, 853)
                if parsed.direction == "outbound":
                    flow.device_ip = parsed.source_ip
                elif parsed.direction == "inbound":
                    flow.device_ip = parsed.destination_ip
                self._flows[key] = flow
            apply_website_to_flow(flow, parsed, self.dns_cache)
            if flow.website and flow.website != "Unknown":
                friendly = service_from_domain(flow.website)
                if friendly:
                    flow.service = friendly
            flow.last_seen = ts_epoch
            flow.last_seen_dt = pkt_ts
            if parsed.direction == "inbound":
                flow.bytes_received += parsed.packet_size
                flow.packets_received += 1
            else:
                flow.bytes_sent += parsed.packet_size
                flow.packets_sent += 1
            return flow, is_new

    def close_stale(self) -> list[Flow]:
        closed = []
        now = time.time()
        with self._lock:
            for key in list(self._flows.keys()):
                flow = self._flows[key]
                if now - flow.last_seen > self.timeout:
                    flow.closed = True
                    del self._flows[key]
                    closed.append(flow)
        for flow in closed:
            if self.on_close:
                self.on_close(flow)
        return closed

    def close_all(self) -> list[Flow]:
        with self._lock:
            flows = list(self._flows.values())
            self._flows.clear()
        for flow in flows:
            flow.closed = True
            if self.on_close:
                self.on_close(flow)
        return flows

    def active_count(self) -> int:
        with self._lock:
            return len(self._flows)

    def active_flows(self) -> list[Flow]:
        with self._lock:
            return list(self._flows.values())


class PacketCaptureManager:
    """Manages the capture thread, flow tracker and callbacks.

    Live mode uses Scapy; demo mode generates synthetic flows so the
    dashboard can still be demonstrated without capture privileges.
    """

    def __init__(self, on_flow_close=None, on_active_update=None):
        self.interface = settings.CAPTURE_INTERFACE or ""
        self.running = False
        self.demo_mode = settings.DEMO_MODE
        self._sniffer = None
        self._thread = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._local_ips: set[str] = set()
        self.dns_cache = DnsCache()
        self.tracker = FlowTracker(
            timeout_seconds=settings.FLOW_TIMEOUT_SECONDS,
            on_close=on_flow_close,
            dns_cache=self.dns_cache,
        )
        self._on_active_update = on_active_update
        self._flush_interval = settings.FLUSH_INTERVAL_SECONDS
        self._last_error = None

    @property
    def is_running(self) -> bool:
        return self.running

    def set_demo_mode(self, enabled: bool):
        self.demo_mode = enabled
        if enabled:
            self.stop()

    def set_interface(self, interface: str):
        self.interface = interface
        if self.running and not self.demo_mode:
            self.stop()
            self.start()

    def list_interfaces(self) -> list[dict]:
        try:
            ifaces = conf.ifaces.values()
            results = []
            for iface in ifaces:
                if not isinstance(iface, NetworkInterface):
                    continue
                ip = getattr(iface, "ip", None)
                results.append({
                    "name": iface.name,
                    "description": iface.description or "",
                    "ip": ip,
                    "mac": iface.mac,
                })
            if not results:
                return [{"name": n, "description": n, "ip": None, "mac": None} for n in get_if_list()]
            return results
        except Exception as exc:  # pragma: no cover - depends on host OS
            logger.warning("Failed to list interfaces: %s", exc)
            return [{"name": n, "description": n, "ip": None, "mac": None} for n in get_if_list()]

    def _detect_local_ips(self):
        ips = set()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
            s.close()
        except OSError:
            pass
        try:
            ips.add(socket.gethostbyname(socket.gethostname()))
        except OSError:
            pass
        for iface in self.list_interfaces():
            if iface.get("ip"):
                ips.add(iface["ip"])
        if self.interface:
            for iface in self.list_interfaces():
                if iface.get("name") == self.interface and iface.get("ip"):
                    ips.add(iface["ip"])
        self._local_ips = ips
        self.tracker.set_local_ips(ips)
        logger.info("Detected local IPs: %s", sorted(ips))
        return ips

    def start(self):
        with self._lock:
            if self.running:
                return
            self.running = True
            self._stop_event.clear()
            self._detect_local_ips()
            if self.demo_mode:
                # Shorter flow timeout in demo mode so connections close quickly,
                # generating history records, privacy alerts and reports.
                self.tracker.timeout = min(self.tracker.timeout, 6.0)
                self._thread = threading.Thread(target=self._demo_loop, daemon=True)
            else:
                self.tracker.timeout = settings.FLOW_TIMEOUT_SECONDS
                self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            logger.info("Monitoring started (mode=%s, interface=%s)",
                        "DEMO" if self.demo_mode else "live", self.interface or "auto")

    def stop(self):
        with self._lock:
            if not self.running:
                return
            self.running = False
            self._stop_event.set()
        if self._sniffer is not None:
            try:
                self._sniffer.stop()
            except Exception:
                pass
        # Give the thread a moment to shut down cleanly, then flush remaining flows.
        self._stop_event.wait(timeout=2.0)
        self.tracker.close_all()
        self.tracker.timeout = settings.FLOW_TIMEOUT_SECONDS
        logger.info("Monitoring stopped")

    def _sniff_callback(self, pkt):
        try:
            for ip, domain, ttl in extract_dns_metadata(pkt):
                self.dns_cache.record(ip, domain, ttl)
            parsed = parse_packet(pkt, interface=self.interface, local_ips=self._local_ips)
            if parsed is None:
                return
            parsed.sni = extract_tls_sni(pkt)
            flow, is_new = self.tracker.process_parsed(parsed)
            if flow is not None and self._on_active_update:
                self._on_active_update(flow, is_new=is_new)
        except Exception as exc:  # pragma: no cover
            logger.warning("Packet processing error: %s", exc)

    def _capture_loop(self):
        try:
            kwargs = {"prn": self._sniff_callback, "store": False}
            if self.interface:
                kwargs["iface"] = self.interface
            self._sniffer = AsyncSniffer(**kwargs)
            self._sniffer.start()
            last_flush = time.time()
            while not self._stop_event.is_set():
                self.tracker.close_stale()
                if self._on_active_update:
                    self._on_active_update(None, is_new=False, tick=True)
                time.sleep(self._flush_interval)
                last_flush = time.time()
        except PermissionError as exc:
            self._last_error = f"Permission denied: {exc}"
            logger.error("Capture permission error: %s", exc)
            self.running = False
        except Exception as exc:  # pragma: no cover
            self._last_error = str(exc)
            logger.error("Capture error: %s", exc)
            self.running = False
        finally:
            if self._sniffer is not None:
                try:
                    self._sniffer.stop()
                except Exception:
                    pass

    def _demo_loop(self):
        """Generates clearly-labeled synthetic traffic for demonstration.

        Each synthetic event gets its own capture timestamp derived from a
        synthetic schedule (wall clock plus a small per-flow offset), so demo
        flows never share an identical timestamp and progress realistically.

        Flows are kept alive across several ticks (same source port, matching
        a real connection) and then rotated, so persisted demo connections
        carry real start/end times and non-zero durations.
        """
        import random

        DEMO_TARGETS = [
            ("Google", "142.250.190.46", 443, "TCP", True, "google.com"),
            ("YouTube", "142.250.190.78", 443, "TCP", True, "youtube.com"),
            ("Microsoft", "13.107.42.14", 443, "TCP", True, "microsoft.com"),
            ("DNS", "8.8.8.8", 53, "UDP", False, "dns.google"),
            ("Local HTTP", "192.168.1.1", 8000, "TCP", False, None),
            ("Cloudflare", "104.18.20.8", 443, "TCP", True, "cloudflare.com"),
        ]
        # Seed the DNS cache so demo traffic flows through the same
        # website-resolution pipeline used in live capture.
        for name, dst, port, proto, enc, domain in DEMO_TARGETS:
            if domain:
                self.dns_cache.record(dst, domain, ttl=600)
        # Per-target source-port state so a flow lives for a few ticks before
        # rotating to a fresh one (that then closes with a real duration).
        port_state = {
            i: {"port": random.randint(1024, 60000), "age": 0}
            for i in range(len(DEMO_TARGETS))
        }
        tick = settings.DEMO_TICK_SECONDS
        last_flush = time.time()
        while not self._stop_event.is_set():
            now = time.time()
            for i, (name, dst, port, proto, enc, domain) in enumerate(DEMO_TARGETS):
                state = port_state[i]
                # Demo flow lifetime ≈ 4 ticks, then rotate to a new flow.
                if state["age"] >= 4:
                    state["port"] = random.randint(1024, 60000)
                    state["age"] = 0
                state["age"] += 1
                parsed = type("DemoParsed", (), {})()
                parsed.source_ip = next(iter(self._local_ips or {"192.168.1.10"}))
                parsed.destination_ip = dst
                parsed.source_port = state["port"]
                parsed.destination_port = port
                parsed.protocol = proto
                parsed.encrypted = enc
                parsed.direction = "outbound"
                parsed.packet_size = random.randint(80, 1400)
                parsed.service = name
                parsed.sni = None
                # Synthetic event schedule: consecutive flows get distinct
                # capture times that progress within (and across) each tick.
                parsed.timestamp = demo_event_time(now, i)
                flow, is_new = self.tracker.process_parsed(parsed)
                if flow is not None:
                    flow.service = name
                    flow.encrypted = enc
                    if self._on_active_update:
                        self._on_active_update(flow, is_new=is_new)
            self.tracker.close_stale()
            time.sleep(max(0.05, tick - (time.time() - now)))
            if time.time() - last_flush > self._flush_interval:
                last_flush = time.time()
                if self._on_active_update:
                    self._on_active_update(None, is_new=False, tick=True)