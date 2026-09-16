# 🛡️ Network Privacy Monitoring & Communication Transparency Dashboard

<div align="center">

### 🔐 See What Your Device Communicates — Without Inspecting Private Content

A **production-quality full-stack network privacy monitoring dashboard** that provides real-time visibility into network metadata, encryption, traffic usage, services, connections, privacy scores, and unencrypted communication.

<br>

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge\&logo=react\&logoColor=black)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge\&logo=sqlite\&logoColor=white)
![Scapy](https://img.shields.io/badge/Scapy-Packet%20Capture-FF6F00?style=for-the-badge)
![WebSocket](https://img.shields.io/badge/WebSocket-Realtime-7C3AED?style=for-the-badge)

<br>

![Status](https://img.shields.io/badge/Status-Production%20Ready-22C55E?style=flat-square)
![Privacy](https://img.shields.io/badge/Privacy-Metadata%20Only-06B6D4?style=flat-square)
![Demo](https://img.shields.io/badge/Demo%20Mode-Available-F59E0B?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-6366F1?style=flat-square)

</div>

---

## 🌐 What Is This?

The **Network Privacy Monitoring & Communication Transparency Dashboard** answers a simple question:

> 🔎 **What is my device communicating with, how much data is being transmitted, what protocols/services are being used, and is the communication encrypted?**

The application captures and analyzes **network metadata only**.

It does **not** inspect, decrypt, or store private communication content.

### 🔐 Privacy First

```text
📡 Network Traffic
       ↓
📦 Metadata Extraction
       ↓
🔄 Flow Aggregation
       ↓
🔍 Protocol & Service Analysis
       ↓
🔐 Encryption Analysis
       ↓
📊 Privacy Score
       ↓
🖥️ Real-Time Dashboard
```

### 🚫 Never Stored

* ❌ Passwords
* ❌ Messages
* ❌ Cookies
* ❌ HTTP bodies
* ❌ File contents
* ❌ Authentication tokens
* ❌ Private communication payloads

---

# ✨ Features

| Feature                           | Description                                                 |
| --------------------------------- | ----------------------------------------------------------- |
| 🟢 **Real-Time Monitoring**       | Live packet capture with continuous dashboard updates       |
| ⚡ **WebSocket Streaming**         | Real-time traffic pushed directly to the dashboard          |
| 🔄 **Automatic Reconnect**        | WebSocket reconnect with REST polling fallback              |
| 🌐 **Website Identification**     | Reliable domain identification using observable metadata    |
| 🧩 **Application Identification** | Applications remain `Unknown` unless reliably identifiable  |
| 🧠 **DNS Intelligence**           | Expiring IP → domain mappings honoring DNS TTL              |
| 📊 **Traffic Analytics**          | Upload, download, speed and traffic-over-time visualization |
| 🔐 **Encryption Analysis**        | Identifies whether encryption is observable                 |
| 🚨 **Privacy Alerts**             | Alerts for HTTP and other unencrypted communication         |
| 🏢 **Service Detection**          | HTTP, HTTPS/TLS, DNS, SSH, SMTP and known providers         |
| 🎯 **Privacy Score**              | Transparent configurable 0–100 privacy score                |
| 🕒 **Connection History**         | Searchable and filterable historical flows                  |
| 💻 **Device Monitoring**          | Traffic and top services/websites per device                |
| 📑 **Reports**                    | Daily, weekly and custom-range reports                      |
| 📥 **CSV Export**                 | Export connection history                                   |
| 📄 **PDF Reports**                | Professional PDF reports using ReportLab                    |
| 🧪 **Demo Mode**                  | Synthetic traffic using the same real-time pipeline         |
| 🗄️ **Data Retention**            | Configurable history retention                              |
| 🌙 **Dark / Light Mode**          | Responsive modern dashboard                                 |

---

# 🏗️ Architecture

```text
                         🌍 NETWORK
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Network Interface   │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Packet Capture    │
                  │       Scapy         │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Packet Parser     │
                  │   Metadata Only     │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    Flow Tracker     │
                  └──────────┬──────────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
       ┌───────────┐   ┌────────────┐   ┌──────────────┐
       │ Protocol  │   │  Service   │   │ Encryption   │
       │ Analysis  │   │Identification│  │   Analysis   │
       └─────┬─────┘   └──────┬─────┘   └──────┬───────┘
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                  ┌─────────────────────┐
                  │ Traffic Statistics  │
                  │  + Privacy Score    │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │       SQLite        │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │       FastAPI       │
                  └──────────┬──────────┘
                             │
                   ┌─────────┴─────────┐
                   ▼                   ▼
             REST API             WebSocket
                   │                   │
                   └─────────┬─────────┘
                             ▼
                  ┌─────────────────────┐
                  │   React Dashboard   │
                  └──────────┬──────────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
         📊 Live View    🕒 History       📑 Reports
```

---

# 🧰 Tech Stack

## 🔙 Backend

| Technology         | Purpose                      |
| ------------------ | ---------------------------- |
| 🐍 **Python**      | Core backend                 |
| ⚡ **FastAPI**      | REST API + WebSocket server  |
| 📡 **Scapy**       | Packet capture and parsing   |
| 🗃️ **SQLAlchemy** | Database ORM                 |
| 🪶 **SQLite**      | Metadata storage             |
| 📄 **ReportLab**   | PDF generation               |
| 🐼 **Pandas**      | Data processing / CSV export |
| 🔌 **Uvicorn**     | ASGI server                  |

## 🎨 Frontend

| Technology       | Purpose                    |
| ---------------- | -------------------------- |
| ⚛️ **React**     | UI framework               |
| ⚡ **Vite**       | Frontend development/build |
| 📈 **Recharts**  | Data visualization         |
| 🌐 **Axios**     | REST API communication     |
| 🔌 **WebSocket** | Real-time updates          |

---

# 🔐 Privacy & Security Design

This project follows a **metadata-only architecture**.

### 📦 Captured Metadata

```text
IP Address
Port
Protocol
Packet Size
Direction
Timestamp
DNS Metadata
TLS SNI
```

### 🚫 Payloads Are Never Stored

```text
❌ Passwords
❌ Messages
❌ Cookies
❌ Files
❌ HTTP Bodies
❌ Authentication Tokens
❌ Private Communication Content
```

### 🔒 HTTPS

The system **does not decrypt HTTPS**.

Encryption status is determined only from observable metadata.

---

# 🌐 Website Identification

The dashboard intentionally avoids unreliable guesses.

The identification pipeline is:

```text
TLS SNI Hostname
       ↓
Recent DNS Mapping
       ↓
Known Service / Domain
       ↓
Destination IP
       ↓
Unknown
```

### 🧠 Example

```text
Destination IP
      ↓
DNS Cache
      ↓
google.com
      ↓
Known Provider
      ↓
Google
```

Applications are **never guessed** from ports or domains.

If an application cannot be reliably identified:

```text
Application: Unknown
```

---

# 🧠 Expiring DNS Cache

The dashboard maintains an IP → domain cache.

Mappings expire according to DNS TTL rules.

```text
DNS Response
     │
     ▼
IP → Domain
     │
     ▼
TTL Timer
     │
     ├── Valid → Use Mapping
     │
     └── Expired → Unknown
```

This prevents traffic from being incorrectly attributed to a website after an IP address changes ownership.

Default cache lifetime:

```text
300 seconds
```

---

# 🎯 Privacy Score

The application calculates a transparent **0–100 privacy score**.

The score considers factors such as:

```text
🔐 Encryption
🌐 Protocol
🚨 Unencrypted Communication
```

Configurable weights:

```text
WEIGHT_ENCRYPTION
WEIGHT_PROTOCOL
WEIGHT_UNENCRYPTED
```

The score is **application-defined and transparent**, rather than claiming to be a universal security measurement.

---

# 🚨 Privacy Alerts

The system generates privacy alerts when unencrypted communication is observed.

Example:

```text
⚠️ PRIVACY ALERT

Protocol:
HTTP

Port:
8000

Encryption:
Encryption not detected
```

The project recommends using **local HTTP servers** for demonstrations rather than intentionally accessing insecure third-party websites.

---

# 🧪 Demo Mode

Don't have packet-capture permissions?

No problem.

The project includes a **Demo Mode** that generates synthetic network traffic.

```text
             DEMO TRAFFIC
                  │
                  ▼
        ┌──────────────────┐
        │ Same Processing  │
        │     Pipeline     │
        └────────┬─────────┘
                 │
                 ▼
        📊 Dashboard
        📑 Reports
        🕒 History
        🚨 Alerts
```

Demo traffic is clearly labeled:

```text
🟡 DEMO DATA
```

This allows the complete application to be demonstrated without requiring privileged packet capture.

---

# 📊 Dashboard

The dashboard provides real-time visibility into:

### 📈 Traffic

* Download speed
* Upload speed
* Total traffic
* Traffic over time

### 🔐 Privacy

* Privacy score
* Encryption percentage
* Unencrypted communication
* Privacy alerts

### 🌐 Websites

* Top websites
* Transferred bytes
* Domain information

### 🏢 Services

* HTTP
* HTTPS/TLS
* DNS
* SSH
* SMTP
* Known providers

---

# 🕒 Connection History

Historical network flows are stored in SQLite.

The Connections page supports:

```text
🔎 Search
🔽 Filtering
📅 History
📊 Traffic information
```

Connection records include:

```text
Timestamp
Device
Website
Domain
Application
Destination IP
Port
Protocol
Bytes
Direction
Encryption
```

---

# 💻 Device Monitoring

The Devices section provides visibility into local devices.

For each device:

```text
📱 Device
   │
   ├── 🌐 Top Websites
   ├── 🏢 Top Services
   ├── 📊 Traffic
   └── 🕒 Connection History
```

---

# 📑 Reports & Export

The project supports:

### 📅 Daily Reports

```text
/api/reports/daily
```

### 📆 Weekly Reports

```text
/api/reports/weekly
```

### 🗓️ Custom Reports

```text
/api/reports/custom
```

### 📥 CSV

Export connection history as CSV.

### 📄 PDF

Generate professional PDF reports using **ReportLab**.

---

# 🔌 API

| Method | Endpoint                        | Description                |
| ------ | ------------------------------- | -------------------------- |
| GET    | `/api/health`                   | Health + monitoring status |
| GET    | `/api/interfaces`               | Available interfaces       |
| GET    | `/api/traffic/live`             | Real-time snapshot         |
| GET    | `/api/traffic/history`          | Connection history         |
| GET    | `/api/traffic/summary`          | Traffic totals             |
| GET    | `/api/traffic/over-time`        | Traffic chart data         |
| GET    | `/api/devices`                  | Monitored devices          |
| GET    | `/api/devices/{id}`             | Device details             |
| GET    | `/api/devices/{id}/traffic`     | Device traffic             |
| GET    | `/api/privacy/score`            | Privacy score              |
| GET    | `/api/privacy/encryption`       | Encryption statistics      |
| GET    | `/api/privacy/summary`          | Privacy snapshot           |
| GET    | `/api/services`                 | Identified services        |
| GET    | `/api/services/top`             | Top services               |
| GET    | `/api/websites`                 | Top websites               |
| GET    | `/api/websites/top`             | Website statistics         |
| GET    | `/api/dns/domains`              | DNS mappings               |
| GET    | `/api/alerts`                   | Privacy alerts             |
| GET    | `/api/alerts/unencrypted`       | Unencrypted alerts         |
| GET    | `/api/reports/daily`            | Daily report               |
| GET    | `/api/reports/weekly`           | Weekly report              |
| GET    | `/api/reports/custom`           | Custom report              |
| GET    | `/api/reports/export/csv`       | CSV export                 |
| GET    | `/api/reports/export/pdf`       | PDF export                 |
| GET    | `/api/capture/status`           | Capture status             |
| POST   | `/api/capture/start`            | Start monitoring           |
| POST   | `/api/capture/stop`             | Stop monitoring            |
| POST   | `/api/capture/interface`        | Select interface           |
| GET    | `/api/settings`                 | Current settings           |
| POST   | `/api/settings/score-weights`   | Update score weights       |
| POST   | `/api/settings/demo`            | Toggle demo mode           |
| POST   | `/api/settings/retention`       | Configure retention        |
| POST   | `/api/settings/retention/clear` | Clear old data             |
| WS     | `/ws/traffic`                   | Real-time traffic          |

---

# ⚡ WebSocket Events

The dashboard receives real-time events through:

```text
/ws/traffic
```

Supported events:

| Event                  | Purpose                   |
| ---------------------- | ------------------------- |
| 🟢 `live`              | Full dashboard snapshot   |
| 🔵 `traffic_update`    | New flow started          |
| 🟣 `connection_closed` | Flow closed and persisted |
| 🔴 `alert`             | New privacy alert         |
| 🟡 `monitoring_status` | Monitoring state changed  |

The frontend processes events **incrementally** rather than re-rendering the entire dashboard for every packet.

---

# 📁 Project Structure

```text
network-privacy-monitor/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── monitor.py
│   │   │
│   │   ├── api/
│   │   │   ├── traffic
│   │   │   ├── devices
│   │   │   ├── privacy
│   │   │   ├── services
│   │   │   ├── websites
│   │   │   ├── dns
│   │   │   ├── alerts
│   │   │   ├── reports
│   │   │   ├── capture
│   │   │   └── settings
│   │   │
│   │   ├── capture/
│   │   │   ├── packet_capture.py
│   │   │   ├── packet_parser.py
│   │   │   └── metadata_extractor.py
│   │   │
│   │   ├── analysis/
│   │   │   ├── protocol.py
│   │   │   ├── service.py
│   │   │   ├── encryption.py
│   │   │   ├── traffic.py
│   │   │   ├── privacy_score.py
│   │   │   ├── dns_cache.py
│   │   │   └── website_identifier.py
│   │   │
│   │   ├── database/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── crud.py
│   │   │
│   │   ├── reports/
│   │   │   ├── report_generator.py
│   │   │   └── export.py
│   │   │
│   │   └── websocket/
│   │       └── manager.py
│   │
│   ├── requirements.txt
│   └── run.py
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── App.jsx
│       ├── main.jsx
│       └── index.css
│
├── database/
│   └── network_privacy.db
│
├── reports/
│   ├── daily/
│   └── weekly/
│
├── logs/
│   └── application.log
│
├── tests/
│   ├── test_capture
│   ├── test_parser
│   ├── test_analysis
│   ├── test_privacy_score
│   ├── test_api
│   ├── test_dns_cache
│   ├── test_metadata_extractor
│   ├── test_website_identification
│   ├── test_realtime
│   └── test_websites_api
│
├── .env.example
├── .gitignore
├── README.md
└── start.py
```

---

# ⚙️ Requirements

| Tool              | Version                       |
| ----------------- | ----------------------------- |
| 🐍 Python         | 3.11+                         |
| 🟢 Node.js        | 18+                           |
| 📦 npm            | 9+                            |
| 📡 Packet Capture | Platform permissions required |

---

# 🚀 Installation

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Anshuu1601/network-privacy-monitoring-and-communication-transperency.git

cd network-privacy-monitoring-and-communication-transperency
```

---

## 2️⃣ Backend Setup

```bash
cd backend

python -m venv .venv
```

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows CMD

```bash
.venv\Scripts\activate
```

### Windows PowerShell

```bash
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🎨 Frontend Setup

```bash
cd frontend

npm install
```

---

# ⚙️ Configuration

Copy the environment template:

```bash
cp .env.example .env
```

Important settings:

| Variable                  | Purpose                  |
| ------------------------- | ------------------------ |
| `DATABASE_URL`            | SQLite database path     |
| `API_HOST`                | Backend host             |
| `API_PORT`                | Backend port             |
| `CAPTURE_INTERFACE`       | Network interface        |
| `RETENTION_DAYS`          | Data retention period    |
| `DEMO_MODE`               | Enable demo mode         |
| `DNS_CACHE_TTL_SECONDS`   | DNS cache lifetime       |
| `WS_MIN_INTERVAL_SECONDS` | WebSocket flow throttle  |
| `WEIGHT_ENCRYPTION`       | Encryption score weight  |
| `WEIGHT_PROTOCOL`         | Protocol score weight    |
| `WEIGHT_UNENCRYPTED`      | Unencrypted score weight |
| `CORS_ORIGINS`            | Allowed frontend origins |

---

# ▶️ Running the Application

## 🔙 Backend

```bash
cd backend

uvicorn app.main:app --reload
```

Or:

```bash
python run.py
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🎨 Frontend Development

```bash
cd frontend

npm run dev
```

Open:

```text
http://localhost:5173
```

Vite automatically proxies:

```text
/api
/ws
```

to the backend.

---

# ⚡ One Command

From the project root:

```bash
python start.py
```

Backend + frontend development server:

```bash
python start.py --frontend
```

---

# 🪟 Windows Packet Capture

Windows packet capture requires **Npcap** and appropriate privileges.

Install Npcap and enable:

```text
Install Npcap in WinPcap API-compatible Mode
```

Then run the backend with administrator privileges.

Select the network interface from:

```text
Settings → Capture Interface
```

For example:

```text
Wi-Fi
Ethernet
```

### 🧪 No Administrator Access?

Use:

```text
Settings → Demo Mode
```

The entire dashboard remains functional.

---

# 🐧 Linux Packet Capture

Packet capture requires appropriate raw-network permissions.

Run with elevated privileges:

```bash
sudo uvicorn app.main:app --reload
```

Or grant the required capabilities:

```bash
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

Ubuntu:

```bash
sudo apt install libpcap-dev
```

---

# 🎬 One-Laptop Demonstration

A simple demonstration workflow:

### 1️⃣ Normal HTTPS Traffic

Open several HTTPS websites.

The dashboard displays:

```text
🔐 High encryption percentage
📈 Traffic activity
🌐 Website information
🎯 Privacy score
```

### 2️⃣ Download

Download a file.

Observe:

```text
⬇️ Downloaded data
📊 Traffic chart
⚡ Download speed
```

### 3️⃣ Upload

Upload a file.

Observe:

```text
⬆️ Uploaded data
📊 Traffic chart
```

### 4️⃣ Unencrypted Communication

Start a local HTTP server:

```bash
python -m http.server 8000
```

Open:

```text
http://localhost:8000
```

The dashboard can display:

```text
🚨 Privacy Alert

HTTP
Port: 8000
Encryption: Encryption not detected
```

> ⚠️ Use local servers for the demonstration rather than relying on real insecure third-party websites.

---

# 🧪 Testing

Run the complete test suite:

```bash
pip install -r backend/requirements.txt

python -m pytest tests/ -v
```

Tests cover:

```text
✅ Packet parsing
✅ TCP / UDP
✅ DNS
✅ HTTP / HTTPS
✅ Flow aggregation
✅ Traffic analysis
✅ Privacy scoring
✅ REST API
✅ CSV generation
✅ PDF generation
✅ DNS cache expiry
✅ TLS SNI extraction
✅ Website identification
✅ WebSocket pipeline
✅ Live summary merging
✅ Website APIs
```

---

# 🛠️ Troubleshooting

### ❌ Permission Denied

Use administrator privileges on Windows or `sudo` / appropriate capabilities on Linux.

Alternatively:

```text
Demo Mode
```

---

### ❌ No Packets Captured

Check:

```text
Settings → Capture Interface
```

Make sure the selected interface is the active network connection.

---

### ❌ Wrong Interface

Use:

```text
GET /api/interfaces
```

or the Settings page.

Example:

```text
Wi-Fi (192.168.x.x)
```

---

### ❌ Frontend Cannot Connect

Make sure the backend is running:

```bash
uvicorn app.main:app --reload
```

Check:

```text
API_HOST
API_PORT
```

and the Vite proxy configuration.

---

### ❌ WebSocket Failure

The dashboard automatically falls back to:

```text
REST Polling
```

with a 3-second interval.

The connection indicator shows:

```text
🟢 LIVE
🟡 RECONNECTING
🔵 POLLING
```

---

### ❌ SQLite Locked

Stop packet capture before manipulating the database.

The application uses:

```text
SQLite WAL mode
```

If deleting the database:

```text
1. Stop backend
2. Delete database
3. Restart backend
```

---

# 🗄️ Database

The application uses SQLite:

```text
database/network_privacy.db
```

Tables:

```text
devices
connections
privacy_scores
alerts
reports
```

Frequently queried fields are indexed:

```text
timestamp
device_id
destination_ip
protocol
encrypted
```

---

# 📡 Real-Time Pipeline

One of the core features of the project is the real-time pipeline.

```text
Packet
  ↓
Parser
  ↓
Metadata Extraction
  ↓
Flow Tracker
  ↓
Analysis
  ↓
Database
  ↓
WebSocket
  ↓
React Dashboard
```

The system uses background processing and WebSocket broadcasts to update the dashboard without requiring the user to stop monitoring or refresh the page.

---

# 🔬 Technical Highlights

### 🧩 Metadata-Only Packet Processing

The packet processing layer intentionally extracts metadata rather than application payloads.

### 🧠 Reliable Website Resolution

Website identification prioritizes observable sources instead of guessing.

### ⏳ TTL-Aware DNS Cache

Expired DNS mappings are removed to reduce incorrect domain attribution.

### ⚡ Incremental WebSocket Updates

The dashboard receives individual flow events while periodic snapshots maintain consistency.

### 🗃️ Safe Database Migration

Schema changes use safe `ALTER TABLE` migration logic to preserve existing data.

### 📊 Transparent Privacy Scoring

The scoring mechanism uses configurable weights instead of presenting the score as a universal security standard.

---

# 🧭 Design Philosophy

This project is **not an intrusion detection system**.

It focuses on:

```text
              🔐 PRIVACY VISIBILITY
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
   Encryption      Traffic          Services
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                Privacy Score
                       │
                       ▼
                 User Awareness
```

The goal is to help users understand:

> **"What is my device communicating with?"**

without inspecting the content of those communications.

---

# 📌 Project Highlights

```text
⚡ Real-Time Network Monitoring
🔐 Metadata-Only Privacy Architecture
🌐 Website & Domain Identification
🧠 TTL-Aware DNS Intelligence
📊 Traffic Analytics
🚨 Privacy Alerts
🎯 Transparent Privacy Score
💻 Device Monitoring
📑 PDF & CSV Reports
🧪 Demo Mode
🔌 WebSocket Streaming
🗃️ SQLite Persistence
🎨 Modern React Dashboard
```

---

# 👨‍💻 Author

<div align="center">

### **Ansar Haressa**

Real Estate Entrepreneur • Technology Enthusiast • Full-Stack Developer

[![GitHub](https://img.shields.io/badge/GitHub-Anshuu1601-181717?style=for-the-badge\&logo=github)](https://github.com/Anshuu1601)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ansar%20Haressa-0A66C2?style=for-the-badge\&logo=linkedin\&logoColor=white)](https://www.linkedin.com/in/ansar-haressa-j-43508128/)

</div>

---

# ⭐ If You Like This Project

If this project helped you understand:

```text
Networking
     +
Packet Analysis
     +
Privacy
     +
FastAPI
     +
React
     +
WebSockets
```

consider giving the repository a ⭐ on GitHub.

---

<div align="center">

### 🛡️ Network Privacy Monitoring & Communication Transparency Dashboard

**Understand your network. Protect your privacy.**

`Metadata Only • No Payload Inspection • Real-Time Visibility`

</div>
