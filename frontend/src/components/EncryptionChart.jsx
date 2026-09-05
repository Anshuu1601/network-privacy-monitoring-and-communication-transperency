import React from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

export default function EncryptionChart({ encrypted = 0, unencrypted = 0 }) {
  const data = [
    { name: "Encrypted", value: Math.max(encrypted, 0) },
    { name: "Unencrypted", value: Math.max(unencrypted, 0) },
  ];
  const hasData = data.some((d) => d.value > 0);
  const COLORS = { Encrypted: "#22c55e", Unencrypted: "#ef4444" };

  return (
    <div className="panel">
      <div className="panel-head">
        <div className="card-title">Encryption Status</div>
      </div>
      <div className="chart-container encryption-chart">
        {!hasData ? (
          <div className="chart-empty">No encryption data yet.</div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                  stroke="none"
                >
                  {data.map((entry) => (
                    <Cell key={entry.name} fill={COLORS[entry.name]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name) => [`${value.toFixed(1)}%`, name]}
                  contentStyle={{
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-center">
              <div className="donut-value">{encrypted.toFixed(0)}%</div>
              <div className="donut-label">Encrypted</div>
            </div>
          </>
        )}
      </div>
      <div className="encryption-legend">
        <div className="enc-legend-row">
          <span className="legend-swatch" style={{ background: "#22c55e" }} />
          Encrypted
          <strong>{encrypted.toFixed(1)}%</strong>
        </div>
        <div className="enc-legend-row">
          <span className="legend-swatch" style={{ background: "#ef4444" }} />
          Unencrypted
          <strong>{unencrypted.toFixed(1)}%</strong>
        </div>
      </div>
    </div>
  );
}