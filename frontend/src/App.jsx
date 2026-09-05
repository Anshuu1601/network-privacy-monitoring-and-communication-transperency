import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import { LiveProvider, useLiveContext } from "./context/LiveContext";
import Connections from "./pages/Connections";
import Dashboard from "./pages/Dashboard";
import DeviceDetail from "./pages/DeviceDetail";
import Devices from "./pages/Devices";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

function ConnectionStatusBar() {
  const { connected, usingWs, error } = useLiveContext();
  if (connected) {
    return (
      <div className={`conn-bar ${usingWs ? "ok" : "polling"}`}>
        {usingWs
          ? "● Live updates via WebSocket"
          : "● Live updates via polling (WebSocket unavailable)"}
      </div>
    );
  }
  return <div className="conn-bar error">⚠ Connection to backend lost — {error || "retrying…"}</div>;
}

export default function App() {
  return (
    <LiveProvider>
      <div className="app-shell">
        <Navbar />
        <main className="main-content">
          <ConnectionStatusBar />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/devices" element={<Devices />} />
            <Route path="/devices/:id" element={<DeviceDetail />} />
            <Route path="/connections" element={<Connections />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="app-footer">
          Network Privacy Monitoring &amp; Communication Transparency Dashboard — analyzes network
          metadata only. It does not decrypt or store private communication content.
        </footer>
      </div>
    </LiveProvider>
  );
}