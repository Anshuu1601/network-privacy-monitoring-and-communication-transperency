import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import MetricCard from "../components/MetricCard";
import TrafficChart from "../components/TrafficChart";
import * as api from "../services/api";
import { formatBytes, formatDuration, formatLocalTime } from "../utils";

export default function DeviceDetail() {
  const { id } = useParams();
  const [device, setDevice] = useState(null);
  const [traffic, setTraffic] = useState({ connections: [], over_time: [] });
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const resp = await api.getDeviceTraffic(id, 500);
        if (!cancelled) setTraffic(resp.data);
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    };
    load();
    const timer = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [id]);

  const deviceMeta = traffic.device;
  const encryptedPct = deviceMeta?.encrypted_percentage ?? 0;
  const totalBytes = (deviceMeta?.bytes_sent || 0) + (deviceMeta?.bytes_received || 0);

  const encryptionData = useMemo(() => {
    const enc = traffic.connections.filter((c) => c.encrypted).length;
    const total = traffic.connections.length || 1;
    return { encrypted: (enc / total) * 100, unencrypted: ((total - enc) / total) * 100 };
  }, [traffic.connections]);

  const topWebsites = useMemo(() => {
    const agg = {};
    for (const c of traffic.connections) {
      const key = c.website && c.website !== "Unknown" ? c.website : null;
      if (!key) continue;
      agg[key] = agg[key] || { website: key, bytes: 0, count: 0 };
      agg[key].bytes += (c.bytes_sent || 0) + (c.bytes_received || 0);
      agg[key].count += 1;
    }
    return Object.values(agg)
      .sort((a, b) => b.bytes - a.bytes)
      .slice(0, 8);
  }, [traffic.connections]);

  const topServices = useMemo(() => {
    const agg = {};
    for (const c of traffic.connections) {
      const key = c.service || "Unknown";
      agg[key] = agg[key] || { service: key, bytes: 0, count: 0 };
      agg[key].bytes += (c.bytes_sent || 0) + (c.bytes_received || 0);
      agg[key].count += 1;
    }
    return Object.values(agg)
      .sort((a, b) => b.bytes - a.bytes)
      .slice(0, 8);
  }, [traffic.connections]);

  if (error) {
    return (
      <div className="page">
        <div className="error-banner">⚠ {error}</div>
        <Link to="/devices" className="text-link">← Back to devices</Link>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <Link to="/devices" className="text-link">← Devices</Link>
          <h1>{deviceMeta?.name || "Device"}</h1>
          <p className="page-sub mono">
            {deviceMeta?.ip_address || "—"} · {deviceMeta?.interface || "Unknown interface"}
            {deviceMeta?.hostname ? ` · ${deviceMeta.hostname}` : ""}
          </p>
        </div>
      </div>

      <div className="metric-grid">
        <MetricCard
          title="Privacy Score"
          value={deviceMeta?.privacy_score ?? "—"}
          icon="🛡️"
        />
        <MetricCard
          title="Encrypted"
          value={`${encryptedPct.toFixed(1)}%`}
          icon="🔒"
          tone="good"
        />
        <MetricCard
          title="Uploaded"
          value={formatBytes(deviceMeta?.bytes_sent)}
          icon="⬆️"
        />
        <MetricCard
          title="Downloaded"
          value={formatBytes(deviceMeta?.bytes_received)}
          icon="⬇️"
        />
        <MetricCard
          title="Active Connections"
          value={deviceMeta?.active_connections ?? 0}
          icon="🔗"
        />
        <MetricCard title="Total Data" value={formatBytes(totalBytes)} icon="⇅" />
      </div>

      <TrafficChart data={traffic.over_time || []} />

      <div className="grid-2">
        <div className="panel">
          <div className="panel-head">
            <div className="card-title">Top Websites</div>
            <span className="muted-count">{topWebsites.length}</span>
          </div>
          {topWebsites.length === 0 ? (
            <div className="chart-empty">No websites identified yet.</div>
          ) : (
            <ul className="service-list">
              {topWebsites.map((s) => (
                <li key={s.website}>
                  <span className="service-name">{s.website}</span>
                  <span className="service-count">{s.count} conn</span>
                  <span className="service-bytes">{formatBytes(s.bytes)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="panel">
          <div className="panel-head">
            <div className="card-title">Top Services</div>
            <span className="muted-count">{topServices.length}</span>
          </div>
          {topServices.length === 0 ? (
            <div className="chart-empty">No services identified yet.</div>
          ) : (
            <ul className="service-list">
              {topServices.map((s) => (
                <li key={s.service}>
                  <span className="service-name">{s.service}</span>
                  <span className="service-count">{s.count} conn</span>
                  <span className="service-bytes">{formatBytes(s.bytes)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <div className="card-title">Connection History</div>
          <span className="muted-count">{traffic.connections.length} flows</span>
        </div>
        {traffic.connections.length === 0 ? (
          <div className="chart-empty">No connections recorded yet.</div>
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
                {traffic.connections.slice(0, 100).map((c) => (
                  <tr key={c.id}>
                    <td title={c.timestamp ? new Date(c.timestamp).toLocaleString() : ""}>{formatLocalTime(c.timestamp)}</td>
                    <td className="cell-service">{c.service || "Unknown"}</td>
                    <td className="cell-service">{c.website && c.website !== "Unknown" ? c.website : "—"}</td>
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