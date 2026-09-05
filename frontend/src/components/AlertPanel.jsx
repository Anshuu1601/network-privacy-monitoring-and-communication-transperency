import React from "react";
import { formatTime } from "../utils";

export default function AlertPanel({ alerts = [], title = "Privacy Alerts" }) {
  const visible = alerts.slice(0, 8);
  return (
    <div className="panel">
      <div className="panel-head">
        <div className="card-title">⚠ {title}</div>
        {alerts.length > 0 && <span className="muted-count">{alerts.length}</span>}
      </div>
      {visible.length === 0 ? (
        <div className="chart-empty">
          No privacy alerts. Unencrypted HTTP communication will appear here.
        </div>
      ) : (
        <ul className="alert-list">
          {visible.map((a) => (
            <li key={a.id} className={`alert-item alert-${(a.severity || "warning").toLowerCase()}`}>
              <div className="alert-line">
                <span className="badge badge-alert">{a.severity || "WARNING"}</span>
                <span className="alert-time">{formatTime(a.timestamp)}</span>
              </div>
              <div className="alert-msg">{a.message}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}