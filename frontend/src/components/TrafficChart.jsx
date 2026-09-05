import React from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatBytes, formatLocalTime, formatLocalTimeHourMinute } from "../utils";

export default function TrafficChart({ data = [], loading = false }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <div className="card-title">Real-Time Traffic</div>
        <div className="legend">
          <span className="legend-item">
            <span className="legend-swatch swatch-upload" /> Upload
          </span>
          <span className="legend-item">
            <span className="legend-swatch swatch-download" /> Download
          </span>
        </div>
      </div>
      <div className="chart-container">
        {loading && data.length === 0 ? (
          <div className="chart-empty">Loading traffic data…</div>
        ) : data.length === 0 ? (
          <div className="chart-empty">
            No traffic yet. Start monitoring to see real-time upload / download.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gUpload" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.05} />
                </linearGradient>
                <linearGradient id="gDownload" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22c55e" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="time"
                tickFormatter={formatLocalTimeHourMinute}
                stroke="var(--muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tickFormatter={formatBytes}
                stroke="var(--muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={56}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value, name) => [
                  formatBytes(value),
                  name === "upload" ? "Upload" : "Download",
                ]}
                labelFormatter={formatLocalTime}
              />
              <Area
                type="monotone"
                dataKey="upload"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#gUpload)"
              />
              <Area
                type="monotone"
                dataKey="download"
                stroke="#22c55e"
                strokeWidth={2}
                fill="url(#gDownload)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
