import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatBytes } from "../utils";

const COLORS = ["#06b6d4", "#3b82f6", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444"];

export default function WebsiteList({ websites = [] }) {
  const data = (websites || []).map((s, i) => ({
    name: s.website || "Other",
    bytes: s.bytes || 0,
    count: s.count || 0,
    color: COLORS[i % COLORS.length],
  }));

  return (
    <div className="panel">
      <div className="panel-head">
        <div className="card-title">Top Websites</div>
      </div>
      {data.length === 0 ? (
        <div className="chart-empty">No websites identified yet.</div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={210}>
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="name"
                stroke="var(--muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                interval={0}
                angle={-12}
                textAnchor="end"
                height={50}
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
                  name === "bytes" ? formatBytes(value) : value,
                  name === "bytes" ? "Data" : "Connections",
                ]}
              />
              <Bar dataKey="bytes" radius={[6, 6, 0, 0]}>
                {data.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <ul className="service-list">
            {data.map((s) => (
              <li key={s.name}>
                <span className="service-dot" style={{ background: s.color }} />
                <span className="service-name">{s.name}</span>
                <span className="service-count">{s.count} conn</span>
                <span className="service-bytes">{formatBytes(s.bytes)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}