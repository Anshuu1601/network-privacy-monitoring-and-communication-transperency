# Network Privacy Monitoring & Communication Transparency Dashboard

A production-quality full-stack application that monitors **network metadata** in real time and
answers the question:

> *What is my device communicating with, how much data is being transmitted, what
> protocols/services are being used, and is the communication encrypted?*

The dashboard provides **privacy visibility** — encryption status, data usage, services,
connection history, privacy scores, and alerts for unencrypted communication — plus downloadable
CSV/PDF reports. It is **not** an attack-detection system.

---

## Project Overview

The system captures packets from your network interface, extracts **only metadata**
(IPs, ports, protocol, packet sizes, direction — never payloads, messages, cookies or file
contents), aggregates packets into *flows*, analyzes encryption and services, computes a
transparent privacy score, and publishes everything to a modern React dashboard over a WebSocket
connection.

A **Demo Mode** generates clearly-labeled synthetic traffic so the project can be demonstrated
even when packet-capture permissions are unavailable.

---

## Features

- **Real-time monitoring** — live packet capture; flows, metrics and the privacy score update on
  the dashboard *while* capture is running (WebSocket push, no stop/refresh required)
- **Real-time connection status** — `LIVE` / `RECONNECTING` / `POLLING` indicator with automatic
  WebSocket reconnect and REST-polling fallback
- **Website / domain identification** — privacy-preserving, reliable-only naming from **TLS SNI
  hostname → recent DNS mapping → known service/domain → destination IP → Unknown**
- **Website vs Application** — separate fields; applications are **never guessed** and stay
  `Unknown` unless reliably identifiable
- **Expiring DNS cache** — IP→domain mappings honor DNS TTL (short default) so traffic is never
  attributed to the wrong site after an IP changes hands
- **Traffic visibility** — upload/download, speeds, traffic over time
- **Encryption status** — observable encryption labeling (`Encryption detected` /
  `Encryption not detected`)
- **Service identification** — HTTP, HTTPS/TLS, DNS, SSH, SMTP, plus friendly labels for known
  providers (Google, YouTube, GitHub, Microsoft, Cloudflare, …)
- **Privacy score** — transparent application-defined 0–100 score with configurable weights
- **Unencrypted communication alerts** — `Privacy Alert` (INFO/WARNING) for HTTP & similar
- **Connection history** — searchable, filterable flow history stored in SQLite (with Website,
  Domain and Application columns)
- **Devices** — local device monitoring with top websites/services per device
- **Reports** — daily, weekly and custom-range reports
- **Export** — connection history as CSV; professional PDF reports (ReportLab)
- **Demo Mode** — synthetic, clearly-labeled data run through the *same* real-time pipeline
- **Data retention** — configurable retention with confirmed data clearing
- **Dark / light mode** — responsive professional dashboard

---

## Architecture

```
                    NETWORK
                       |
                       v
              Network Interface
                       |
                       v
                Packet Capture        (Scapy, background thread)
                       |
                       v
                Packet Parser         (metadata only — no payloads)
                       |
                       v
                 Flow Tracker         (packets → one connection record)
                       |
          +------------+------------+
          |            |            |
          v            v            v
      Protocol      Service       Encryption
      Analysis   Identification   Analysis
          |            |            |
          +------------+------------+
                       |
                       v
              Traffic Stats + Privacy Score
                       |
                       v
                    SQLite
                       |
                       v
                    FastAPI
                       |
              +--------+--------+
              |                 |
              v                 v
        REST API            WebSocket   (/ws/traffic)
              |                 |
              +--------+--------+
                       |
                       v
                React Dashboard
                       |
          +------------+-------------+
          |            |             |
          v            v             v
      Live View     History       Reports
```

### Backend (`backend/`)

- **FastAPI + Uvicorn** — REST API and WebSocket server
- **Scapy** — packet capture (`app/capture/packet_capture.py`), parsing
  (`app/capture/packet_parser.py`) and metadata extraction (`app/capture/metadata_extractor.py`)
  — DNS responses and TLS SNI are read as observable metadata (never decrypted)
- **Analysis modules** (`app/analysis/`) — protocol, service, encryption, traffic, privacy score,
  expiring **DNS cache** (`dns_cache.py`) and website resolution (`website_identifier.py`)
- **SQLAlchemy + SQLite** — metadata storage (`app/database/`); safe `ALTER TABLE` migration
  preserves existing data when new columns are added
- **ReportLab + Pandas** — PDF and CSV export (`app/reports/`)
- **WebSocket manager** (`app/websocket/manager.py`) — thread-safe broadcasts scheduled onto the
  running event loop

### Frontend (`frontend/`)

- **React + Vite** — SPA dashboard
- **Recharts** — traffic, encryption and service charts
- **Axios** — REST calls; **WebSocket** — live updates with polling fallback
- Pages: Dashboard, Devices (+ detail), Connections, Reports, Settings

### Database (`database/network_privacy.db`)

Tables: `devices`, `connections`, `privacy_scores`, `alerts`, `reports` — with indexes on
frequently queried columns (`timestamp`, `device_id`, `destination_ip`, `protocol`, `encrypted`).

---

## Requirements

| Tool | Version |
| --- | --- |
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Packet-capture permissions | See Windows / Linux notes below |

---

## Installation

### 1. Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

- **Windows (CMD):** `.venv\Scripts\activate`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Linux / macOS:** `source .venv/bin/activate`

Then install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Frontend

```bash
cd frontend
npm install
```

### 3. Configuration

Copy `.env.example` to `.env` in the project root and adjust values if needed:

```bash
cp .env.example .env
```

Key settings:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLite path (default `sqlite:///./database/network_privacy.db`) |
| `API_HOST` / `API_PORT` | Backend bind address (default `127.0.0.1:8000`) |
| `CAPTURE_INTERFACE` | Leave empty for auto-detect, or set e.g. `Wi-Fi` / `eth0` |
| `RETENTION_DAYS` | History retention period (0 = unlimited) |
| `DEMO_MODE` | Start in demo mode (`true`/`false`) |
| `DNS_CACHE_TTL_SECONDS` | IP→domain cache lifetime (default `300`) |
| `WS_MIN_INTERVAL_SECONDS` | Min gap between individual flow WebSocket events (default `1.0`) |
| `WEIGHT_ENCRYPTION`, `WEIGHT_PROTOCOL`, `WEIGHT_UNENCRYPTED` | Privacy score weights |
| `CORS_ORIGINS` | Allowed frontend origins (comma separated) |

---

## Running

### Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Or use the launcher:

```bash
python run.py
```

The API is available at `http://127.0.0.1:8000` (interactive docs at `/docs`).

> **Tip — single URL:** if `frontend/dist` exists (run `npm run build` once in `frontend/`),
> the backend also serves the built dashboard at `http://127.0.0.1:8000`. You only need one
> terminal for a complete demo. Use `npm run dev` when you are actively developing the UI.

### Frontend (development mode)

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` and `/ws` to the backend, so no extra CORS
setup is needed in development.

### One command

```bash
python start.py          # backend only
python start.py --frontend   # backend + frontend dev server
```

---

## Windows Instructions

**Packet capture permissions**

Scapy/Npcap on Windows require **administrator privileges** to capture packets:

1. Install **Npcap** from https://npcap.com (check *"Install Npcap in WinPcap API-compatible Mode"*).
2. Run the backend **as Administrator**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
3. In the **Settings** page, select your capture interface (e.g. `Wi-Fi`, `Ethernet`) and click
   **Start Monitoring**.

If you cannot run as Administrator, use **Demo Mode** from the Settings page — the dashboard
still works end-to-end with synthetic, clearly-labeled data.

**Where the demo data goes:** demo flows are stored through the same pipeline and are clearly
marked `DEMO DATA` in the UI, so reports and history remain functional for the presentation.

---

## Linux Instructions

Capture requires the `AF_PACKET` socket which needs root, or the `CAP_NET_RAW` capability:

```bash
# run as root
sudo uvicorn app.main:app --reload

# or grant the capability (replace <user> with your user)
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

On Ubuntu install libpcap if prompted:

```bash
sudo apt install libpcap-dev
```

Select the interface in **Settings** (e.g. `wlan0`, `eth0`) and start monitoring.

---

## One-Laptop Demonstration Guide

1. **Normal traffic** — open a few HTTPS websites; the dashboard shows high encryption
   percentage and privacy score.
2. **Download** — download a file; the *Downloaded* metric and traffic chart update.
3. **Upload** — upload a file; the *Uploaded* metric updates.
4. **Unencrypted demonstration** — start a local HTTP server and open it in the browser:
   ```bash
   python -m http.server 8000
   ```
   Access `http://localhost:8000` (or your LAN IP). The dashboard shows a **Privacy Alert**:
   HTTP communication on port 8000 with *Encryption not detected*.
   *(Use only local servers — never rely on real insecure third-party sites.)*

> The project analyzes **network metadata only**. It does not decrypt traffic, does not store
> payloads, passwords, messages, cookies or file contents, and does not perform attack
> detection.

---

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Health + monitoring status |
| GET | `/api/interfaces` | Available capture interfaces |
| GET | `/api/traffic/live` | Full real-time snapshot |
| GET | `/api/traffic/history` | Connection history (paginated) |
| GET | `/api/traffic/summary` | Totals / active connections |
| GET | `/api/traffic/over-time` | Chart buckets |
| GET | `/api/devices` | Monitored devices |
| GET | `/api/devices/{id}` | Device detail |
| GET | `/api/devices/{id}/traffic` | Device traffic + chart |
| GET | `/api/privacy/score` | Current privacy score + reasons |
| GET | `/api/privacy/encryption` | Encryption statistics |
| GET | `/api/privacy/summary` | Full privacy snapshot |
| GET | `/api/services` | Identified services |
| GET | `/api/services/top` | Top services (bucketed) |
| GET | `/api/websites` | Top websites by transferred bytes |
| GET | `/api/websites/top` | Top websites (bucketed) |
| GET | `/api/dns/domains` | Current DNS IP→domain mappings (expiring cache) |
| GET | `/api/alerts` | Recent privacy alerts |
| GET | `/api/alerts/unencrypted` | Unencrypted-communication alerts |
| GET | `/api/reports/daily` | Today's report |
| GET | `/api/reports/weekly` | Weekly report |
| GET | `/api/reports/custom` | Custom date range (`start`, `end`) |
| GET | `/api/reports/export/csv` | Connection history CSV |
| GET | `/api/reports/export/pdf` | PDF report (`report_type`, `start`, `end`) |
| GET | `/api/capture/status` | Capture status |
| POST | `/api/capture/start` | Start monitoring (`{ "mode": "live" \| "demo" }`) |
| POST | `/api/capture/stop` | Stop monitoring |
| POST | `/api/capture/interface` | Select interface |
| GET | `/api/settings` | Current settings |
| POST | `/api/settings/score-weights` | Update privacy-score weights |
| POST | `/api/settings/demo` | Toggle demo mode |
| POST | `/api/settings/retention` | Set retention days |
| POST | `/api/settings/retention/clear` | Clear old data (needs day count) |
| WS | `/ws/traffic` | Real-time traffic updates |

### WebSocket event types (`/ws/traffic`)

| Type | Payload | Meaning |
| --- | --- | --- |
| `live` | full snapshot (`summary`, `privacy_score`, `active_connections`, `alerts`, `websites`, `monitoring`) | Periodic batched snapshot (every `FLUSH_INTERVAL_SECONDS`) and on connect |
| `traffic_update` | `connection` (single flow) | A new flow started (throttled to `WS_MIN_INTERVAL_SECONDS`) |
| `connection_closed` | `connection` (closed flow) | A flow closed and was persisted |
| `alert` | `alert` | A new privacy alert (e.g. unencrypted communication) |
| `monitoring_status` | `monitoring` | Monitoring started/stopped |

The dashboard applies events **incrementally** (no full re-render per packet) and keeps the
dashboard correct via the periodic `live` snapshot.

---

## Testing

```bash
# from the project root, with the venv active
pip install -r backend/requirements.txt
python -m pytest tests/ -v
```

The suite covers packet parsing (TCP/UDP/DNS/HTTP/HTTPS), flow aggregation, traffic analysis,
privacy scoring (100% / 0% / mixed / empty), the full REST API, CSV/PDF generation, the DNS
cache (mapping + expiry), metadata extraction (DNS responses + TLS SNI), website identification
(priority chain, application stays Unknown), the real-time WebSocket pipeline (broadcast
scheduling + live summary merging) and the new `/api/websites` and `/api/dns/domains` endpoints.

---

## Troubleshooting

**Permission denied on capture**
Run the backend as Administrator (Windows) or with `sudo` / `CAP_NET_RAW` (Linux). Or use
Demo Mode.

**No packets captured**
Confirm the correct interface is selected in **Settings**. On Windows, Npcap must be installed
in WinPcap-compatible mode. Check `logs/application.log`.

**Wrong interface**
Use `GET /api/interfaces` (or the Settings page) to list interfaces; select the one with your
IP (e.g. `Wi-Fi (192.168.x.x)`).

**CORS problems**
The dev setup proxies through Vite so CORS should not occur. If accessing from another origin,
add it to `CORS_ORIGINS` in `.env` and restart the backend.

**Frontend cannot connect to backend**
Start the backend first (`uvicorn app.main:app`). Check that `API_HOST`/`API_PORT` match the
Vite proxy target in `frontend/vite.config.js`. If you open the built dashboard served by the
backend itself at `http://127.0.0.1:8000`, no proxy is needed — API and WebSocket use the same
host.

**WebSocket failure**
The frontend falls back to 3-second REST polling automatically. Check that the backend is
running; the connection bar at the top shows the current transport.

**SQLite errors / locked database**
Stop the capture before manipulating the DB. The connection uses WAL mode. If you delete the
DB file, stop the backend first, then restart — it will be recreated.

**Report generation fails**
Confirm `reportlab` is installed. Check `logs/application.log` for details.

---

## Privacy by Design

- Stores **metadata only** — no payloads, passwords, messages, cookies, file contents,
  HTTP bodies, or tokens.
- **Never decrypts** HTTPS; encryption is reported only from observable metadata.
- Website/domain labels come from **reliable observable metadata only** (TLS SNI hostname or a
  recent DNS mapping). Applications are never guessed from a domain or port.
- DNS mappings **expire quickly** (TTL honored, short default) so traffic is never attributed to
  the wrong site after an IP changes hands.
- Configurable data retention; data is only cleared after explicit confirmation.
- The dashboard states: *"This application analyzes network metadata for privacy visibility. It
  does not decrypt or store private communication content."*

## Project Structure

```
network-privacy-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, monitor.py
│   │   ├── api/        traffic, devices, privacy, services, websites, dns, alerts, reports, capture, settings
│   │   ├── capture/    packet_capture.py, packet_parser.py, metadata_extractor.py
│   │   ├── analysis/   protocol, service, encryption, traffic, privacy_score, dns_cache, website_identifier
│   │   ├── database/   database.py, models.py, crud.py
│   │   ├── reports/    report_generator.py, export.py
│   │   └── websocket/  manager.py
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   └── src/
│       ├── components/ Navbar, MetricCard, PrivacyScore, TrafficChart, EncryptionChart,
│       │               DeviceList, ServiceList, WebsiteList, ConnectionTable, AlertPanel, TrafficUsage
│       ├── pages/      Dashboard, Devices, DeviceDetail, Connections, Reports, Settings
│       ├── services/   api.js
│       └── App.jsx, main.jsx, index.css
├── database/           network_privacy.db (created at runtime)
├── reports/            daily/ weekly/
├── logs/               application.log
├── tests/              test_capture, test_parser, test_analysis, test_privacy_score, test_api,
│                       test_dns_cache, test_metadata_extractor, test_website_identification,
│                       test_realtime, test_websites_api
├── .env.example
├── .gitignore
├── README.md
└── start.py
```