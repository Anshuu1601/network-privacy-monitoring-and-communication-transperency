import React from "react";

export default function MetricCard({ title, value, sub, icon, tone = "default", accent }) {
  return (
    <div className={`metric-card metric-${tone}`}>
      <div className="metric-icon" aria-hidden>
        {icon}
      </div>
      <div className="metric-body">
        <div className="metric-title">{title}</div>
        <div className="metric-value" style={accent ? { color: accent } : undefined}>
          {value}
        </div>
        {sub && <div className="metric-sub">{sub}</div>}
      </div>
    </div>
  );
}
