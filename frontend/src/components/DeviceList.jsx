import React, { useState } from "react";
import { Link } from "react-router-dom";
import { formatBytes } from "../utils";

function DeviceRow({ device, onToggle, expanded }) {
  return (
    <div className={`device-row ${expanded ? "expanded" : ""}`}>
      <div className="device-main" onClick={onToggle}>
        <div className="device-icon">💻</div>
        <div className="device-info">
          <div className="device-name">
            {device.name}
            {device.is_local === 1 && <span className="badge badge-local">This device</span>}
          </div>
          <div className="device-meta mono">
            {device.ip_address || "—"} · {device.interface || "Unknown interface"}
            {device.hostname ? ` · ${device.hostname}` : ""}
          </div>
        </div>
        <div className="device-stats">
          <div className="device-stat">
            <span className="stat-label">Privacy</span>
            <strong>{device.privacy_score ?? "—"}</strong>
          </div>
          <div className="device-stat">
            <span className="stat-label">Encrypted</span>
            <strong>{device.encrypted_percentage?.toFixed(1) ?? "0"}%</strong>
          </div>
          <div className="device-stat">
            <span className="stat-label">Up</span>
            <strong>{formatBytes(device.bytes_sent)}</strong>
          </div>
          <div className="device-stat">
            <span className="stat-label">Down</span>
            <strong>{formatBytes(device.bytes_received)}</strong>
          </div>
          <div className="device-stat">
            <span className="stat-label">Active</span>
            <strong>{device.active_connections ?? 0}</strong>
          </div>
        </div>
        <span className={`chevron ${expanded ? "open" : ""}`}>▾</span>
      </div>
      {expanded && (
        <div className="device-detail">
          <Link to={`/devices/${device.id}`} className="text-link">
            View detailed traffic →
          </Link>
        </div>
      )}
    </div>
  );
}

export default function DeviceList({ devices = [] }) {
  const [expanded, setExpanded] = useState(null);
  if (devices.length === 0) {
    return <div className="chart-empty">No devices monitored yet.</div>;
  }
  return (
    <div className="device-list">
      {devices.map((d) => (
        <DeviceRow
          key={d.id}
          device={d}
          expanded={expanded === d.id}
          onToggle={() => setExpanded(expanded === d.id ? null : d.id)}
        />
      ))}
    </div>
  );
}