import React from "react";
import { Link } from "react-router-dom";
import { formatBytes, formatDuration, formatLocalTime } from "../utils";

function EncryptionBadge({ encrypted }) {
  return encrypted ? (
    <span className="badge badge-encrypted">🔒 Encrypted</span>
  ) : (
    <span className="badge badge-unencrypted">⚠ Unencrypted</span>
  );
}

export default function ConnectionTable({ connections = [], limit = 8, emptyText = "No active connections" }) {
  const rows = connections.slice(0, limit);
  return (
    <div className="panel">
      <div className="panel-head">
        <div className="card-title">Active Communications</div>
        <span className="muted-count">{rows.length}</span>
      </div>
      {rows.length === 0 ? (
        <div className="chart-empty">{emptyText}</div>
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
                <th>Data</th>
                <th>Duration</th>
                <th>Encryption</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c, i) => (
                <tr key={i}>
                  <td title={c.timestamp ? new Date(c.timestamp).toLocaleString() : ""}>{formatLocalTime(c.timestamp)}</td>
                  <td className="cell-service">{c.service || "Unknown"}</td>
                  <td className="cell-service">
                    {c.website && c.website !== "Unknown"
                      ? c.website
                      : c.destination || c.destination_ip || "—"}
                  </td>
                  <td>{c.application || "Unknown"}</td>
                  <td><span className="badge badge-proto">{c.protocol}</span></td>
                  <td className="mono">{c.destination || c.destination_ip || "—"}</td>
                  <td className="mono">{c.port ?? c.destination_port ?? "—"}</td>
                  <td>{formatBytes((c.bytes_sent || 0) + (c.bytes_received || 0))}</td>
                  <td>{formatDuration(c.duration, { active: c.status === "active" })}</td>
                  <td>
                    <EncryptionBadge encrypted={c.encrypted} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="panel-foot">
        <Link to="/connections" className="text-link">View full connection history →</Link>
      </div>
    </div>
  );
}