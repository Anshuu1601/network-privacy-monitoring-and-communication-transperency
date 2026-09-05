import React from "react";

export default function PrivacyScore({ scoreData }) {
  const score = scoreData?.score ?? 0;
  const encrypted = scoreData?.encrypted_percentage ?? 0;
  const reasons = scoreData?.reasons ?? [];

  const getTone = (s) => {
    if (s >= 85) return { color: "#22c55e", label: "Excellent" };
    if (s >= 70) return { color: "#84cc16", label: "Good" };
    if (s >= 50) return { color: "#eab308", label: "Fair" };
    return { color: "#ef4444", label: "Needs attention" };
  };

  const tone = getTone(score);
  const circumference = 2 * Math.PI * 52;

  return (
    <div className="privacy-score-card">
      <div className="privacy-score-head">
        <div>
          <div className="card-title">Privacy Score</div>
          <div className="privacy-score-label" style={{ color: tone.color }}>
            {tone.label}
          </div>
        </div>
      </div>

      <div className="score-ring-wrap">
        <svg viewBox="0 0 120 120" className="score-ring">
          <circle cx="60" cy="60" r="52" fill="none" stroke="var(--border)" strokeWidth="10" />
          <circle
            cx="60"
            cy="60"
            r="52"
            fill="none"
            stroke={tone.color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - score / 100)}
            transform="rotate(-90 60 60)"
          />
          <text x="60" y="57" textAnchor="middle" className="score-big">
            {score}
          </text>
          <text x="60" y="75" textAnchor="middle" className="score-small">
            / 100
          </text>
        </svg>
      </div>

      <div className="encryption-split">
        <div className="split-row">
          <span className="split-label">
            <span className="dot dot-encrypted" /> Encrypted
          </span>
          <strong>{encrypted.toFixed(1)}%</strong>
        </div>
        <div className="split-row">
          <span className="split-label">
            <span className="dot dot-unencrypted" /> Unencrypted
          </span>
          <strong>{(100 - encrypted).toFixed(1)}%</strong>
        </div>
        <div className="split-bar">
          <div className="split-encrypted" style={{ width: `${encrypted}%` }} />
          <div className="split-unencrypted" style={{ width: `${100 - encrypted}%` }} />
        </div>
      </div>

      {reasons.length > 0 && (
        <div className="score-reasons">
          {reasons.map((r, i) => (
            <div key={i} className={`score-reason ${r.startsWith("+") ? "good" : "bad"}`}>
              {r}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
