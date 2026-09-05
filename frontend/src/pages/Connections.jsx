import React, { useEffect, useMemo, useState } from "react";
import * as api from "../services/api";
import {
  formatBytes,
  formatDuration,
  formatLocalDateIso,
  formatLocalDateTime,
  formatLocalTime,
} from "../utils";

const FILTER_KEYS = ["date", "protocol", "service", "encryption"];

export default function Connections() {
  const [connections, setConnections] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [demoMode, setDemoMode] = useState(false);
  const [search, setSearch] = useState("");
  const [deviceFilter, setDeviceFilter] = useState("");
  const [protocolFilter, setProtocolFilter] = useState("");
  const [serviceFilter, setServiceFilter] = useState("");
  const [websiteFilter, setWebsiteFilter] = useState("");
  const [encryptionFilter, setEncryptionFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [connResp, devResp, statusResp] = await Promise.all([
          api.getTrafficHistory(2000),
          api.getDevices(),
          api.getCaptureStatus(),
        ]);
        if (!cancelled) {
          setConnections(connResp.data);
          setDevices(devResp.data);
          setDemoMode(statusResp.data.demo_mode === true);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const protocols = useMemo(
    () => [...new Set(connections.map((c) => c.protocol).filter(Boolean))].sort(),
    [connections]
  );
  const services = useMemo(
    () => [...new Set(connections.map((c) => c.service).filter(Boolean))].sort(),
    [connections]
  );
  const websites = useMemo(
    () =>
      [
        ...new Set(
          connections
            .map((c) => c.website)
            .filter((w) => w && w !== "Unknown")
        ),
      ].sort(),
    [connections]
  );

  const filtered = useMemo(() => {
    return connections.filter((c) => {
      if (deviceFilter && String(c.device_id) !== deviceFilter) return false;
      if (protocolFilter && c.protocol !== protocolFilter) return false;
      if (serviceFilter && c.service !== serviceFilter) return false;
      if (websiteFilter && c.website !== websiteFilter) return false;
      if (encryptionFilter) {
        const wantEncrypted = encryptionFilter === "encrypted";
        if (Boolean(c.encrypted) !== wantEncrypted) return false;
      }
      if (dateFilter && c.timestamp) {
        const rowDate = formatLocalDateIso(c.timestamp);
        if (rowDate !== dateFilter) return false;
      }
      if (search.trim()) {
        const q = search.toLowerCase();
        const haystack = [
          c.source_ip,
          c.destination_ip,
          c.service,
          c.website,
          c.application,
          c.protocol,
          String(c.source_port),
          String(c.destination_port),
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [connections, deviceFilter, protocolFilter, serviceFilter, websiteFilter, encryptionFilter, dateFilter, search]);

  const totals = useMemo(() => {
    const sent = filtered.reduce((a, c) => a + (c.bytes_sent || 0), 0);
    const received = filtered.reduce((a, c) => a + (c.bytes_received || 0), 0);
    const enc = filtered.filter((c) => c.encrypted).length;
    return {
      count: filtered.length,
      sent,
      received,
      encrypted: enc,
      encryptedPct: filtered.length ? (enc / filtered.length) * 100 : 0,
    };
  }, [filtered]);

  const resetFilters = () => {
    setDeviceFilter("");
    setProtocolFilter("");
    setServiceFilter("");
    setWebsiteFilter("");
    setEncryptionFilter("");
    setDateFilter("");
    setSearch("");
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Connection History</h1>
          <p className="page-sub">
            Searchable history of aggregated communication flows. Each row is a flow — thousands
            of packets aggregated into one connection record.
          </p>
        </div>
      </div>

      <div className="filter-bar">
        <input
          className="input"
          placeholder="Search IP, port, service…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="input select"
          value={deviceFilter}
          onChange={(e) => setDeviceFilter(e.target.value)}
        >
          <option value="">All devices</option>
          {devices.map((d) => (
            <option key={d.id} value={String(d.id)}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          className="input select"
          value={protocolFilter}
          onChange={(e) => setProtocolFilter(e.target.value)}
        >
          <option value="">All protocols</option>
          {protocols.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select
          className="input select"
          value={serviceFilter}
          onChange={(e) => setServiceFilter(e.target.value)}
        >
          <option value="">All services</option>
          {services.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          className="input select"
          value={websiteFilter}
          onChange={(e) => setWebsiteFilter(e.target.value)}
        >
          <option value="">All websites</option>
          {websites.map((w) => (
            <option key={w} value={w}>
              {w}
            </option>
          ))}
        </select>
        <select
          className="input select"
          value={encryptionFilter}
          onChange={(e) => setEncryptionFilter(e.target.value)}
        >
          <option value="">All encryption</option>
          <option value="encrypted">Encrypted</option>
          <option value="unencrypted">Unencrypted</option>
        </select>
        <input
          type="date"
          className="input"
          value={dateFilter}
          onChange={(e) => setDateFilter(e.target.value)}
        />
        <button className="btn btn-ghost" onClick={resetFilters}>
          Reset
        </button>
      </div>

      <div className="filter-stats">
        <span>
          <strong>{totals.count}</strong> flows
        </span>
        <span>
          <strong>{totals.encryptedPct.toFixed(1)}%</strong> encrypted
        </span>
        <span>
          <strong>{formatBytes(totals.sent)}</strong> sent
        </span>
        <span>
          <strong>{formatBytes(totals.received)}</strong> received
        </span>
      </div>

      {demoMode && (
        <div className="demo-banner">
          <strong>DEMO DATA</strong> — displaying clearly labeled synthetic traffic generated by
          demo mode. Timestamps reflect the synthetic event schedule, not real packet capture.
        </div>
      )}

      {error && <div className="error-banner">⚠ {error}</div>}

      <div className="panel">
        {loading ? (
          <div className="chart-empty">Loading connection history…</div>
        ) : filtered.length === 0 ? (
          <div className="chart-empty">
            No connections match the current filters.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Service</th>
                  <th>Website/Domain</th>
                  <th>Application</th>
                  <th>Protocol</th>
                  <th>Destination</th>
                  <th>Port</th>
                  <th>Sent</th>
                  <th>Received</th>
                  <th>Duration</th>
                  <th>Encryption</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.id}>
                    <td title={formatLocalDateTime(c.timestamp)}>{formatLocalTime(c.timestamp)}</td>
                    <td className="cell-service">{c.service || "Unknown"}</td>
                    <td className="cell-service">{c.website && c.website !== "Unknown" ? c.website : c.domain && c.domain !== "Unknown" ? c.domain : "—"}</td>
                    <td>{c.application || "Unknown"}</td>
                    <td><span className="badge badge-proto">{c.protocol}</span></td>
                    <td className="mono">{c.destination_ip || "—"}</td>
                    <td className="mono">{c.destination_port ?? "—"}</td>
                    <td>{formatBytes(c.bytes_sent)}</td>
                    <td>{formatBytes(c.bytes_received)}</td>
                    <td>{formatDuration(c.duration, { active: c.status === "active" })}</td>
                    <td>
                      {c.encrypted ? (
                        <span className="badge badge-encrypted">🔒 Encrypted</span>
                      ) : (
                        <span className="badge badge-unencrypted">⚠ Unencrypted</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}