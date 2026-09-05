import React from "react";
import { formatBytes, formatSpeed } from "../utils";

export default function TrafficUsage({ summary = {}, speeds = {} }) {
  const sent = summary?.bytes_sent ?? 0;
  const received = summary?.bytes_received ?? 0;
  const total = sent + received;
  const uploadPct = total > 0 ? (sent / total) * 100 : 50;

  return (
    <div className="panel">
      <div className="panel-head">
        <div className="card-title">Data Usage</div>
      </div>
      <div className="usage-totals">
        <div className="usage-row">
          <span className="usage-label">⬆ Uploaded</span>
          <strong>{formatBytes(sent)}</strong>
        </div>
        <div className="usage-row">
          <span className="usage-label">⬇ Downloaded</span>
          <strong>{formatBytes(received)}</strong>
        </div>
        <div className="usage-row">
          <span className="usage-label">⇅ Total</span>
          <strong>{formatBytes(total)}</strong>
        </div>
      </div>

      <div className="usage-bar">
        <div className="usage-upload" style={{ width: `${uploadPct}%` }} />
        <div className="usage-download" style={{ width: `${100 - uploadPct}%` }} />
      </div>

      <div className="speed-grid">
        <div className="speed-box">
          <div className="speed-value">{formatSpeed(speeds?.upload_bps ?? 0)}</div>
          <div className="speed-label">Upload speed</div>
        </div>
        <div className="speed-box">
          <div className="speed-value">{formatSpeed(speeds?.download_bps ?? 0)}</div>
          <div className="speed-label">Download speed</div>
        </div>
      </div>
    </div>
  );
}