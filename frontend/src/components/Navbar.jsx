import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useLiveContext } from "../context/LiveContext";

export default function Navbar() {
  const { monitoring, demo, connectionStatus } = useLiveContext();
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem("npm-theme");
    return saved ? saved === "dark" : window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    localStorage.setItem("npm-theme", dark ? "dark" : "light");
  }, [dark]);

  const statusLabel =
    connectionStatus === "LIVE"
      ? "LIVE"
      : connectionStatus === "POLLING"
      ? "POLLING"
      : "RECONNECTING";
  const statusClass =
    connectionStatus === "LIVE"
      ? "status-live"
      : connectionStatus === "POLLING"
      ? "status-polling"
      : "status-reconnecting";

  const navItems = [
    { to: "/", label: "Dashboard", icon: "📊" },
    { to: "/devices", label: "Devices", icon: "💻" },
    { to: "/connections", label: "Connections", icon: "🔗" },
    { to: "/reports", label: "Reports", icon: "📄" },
    { to: "/settings", label: "Settings", icon: "⚙️" },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="brand-icon">🛡️</span>
        <div>
          <div className="brand-title">Network Privacy Monitor</div>
          <div className="brand-subtitle">Communication Transparency</div>
        </div>
      </div>

      <div className="nav-links">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </div>

      <div className="navbar-status">
        <button
          className="theme-toggle"
          onClick={() => setDark((d) => !d)}
          title={dark ? "Switch to light mode" : "Switch to dark mode"}
        >
          {dark ? "☀️" : "🌙"}
        </button>
        {demo && <span className="status-chip status-demo">DEMO DATA</span>}
        <span
          className={`status-chip ${statusClass}`}
          title="Real-time connection status"
        >
          <span className="dot" />
          {statusLabel}
        </span>
        <span
          className={`status-chip ${
            monitoring?.running ? "status-live" : "status-off"
          }`}
        >
          <span className="dot" />
          {monitoring?.running ? "MONITORING ACTIVE" : "MONITORING STOPPED"}
        </span>
      </div>
    </nav>
  );
}
