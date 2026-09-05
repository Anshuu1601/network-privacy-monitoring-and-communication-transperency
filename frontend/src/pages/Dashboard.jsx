import React, { useEffect, useMemo, useState } from "react";
import AlertPanel from "../components/AlertPanel";
import ConnectionTable from "../components/ConnectionTable";
import EncryptionChart from "../components/EncryptionChart";
import MetricCard from "../components/MetricCard";
import PrivacyScore from "../components/PrivacyScore";
import ServiceList from "../components/ServiceList";
import TrafficChart from "../components/TrafficChart";
import TrafficUsage from "../components/TrafficUsage";
import WebsiteList from "../components/WebsiteList";
import { useLiveContext } from "../context/LiveContext";
import * as api from "../services/api";
import { formatBytes } from "../utils";

export default function Dashboard() {
  const { summary, privacyScore, activeConnections, alerts, monitoring, demo, websites, connectionStatus, startMonitoring, stopMonitoring } =
    useLiveContext();
  const [overTime, setOverTime] = useState([]);
  const [services, setServices] = useState([]);
  const [loadingChart, setLoadingChart] = useState(true);
  const [busy, setBusy] = useState(false);

  const encryptedPct = summary?.encrypted_percentage ?? 0;

  const speeds = useMemo(() => {
    // Approximate instantaneous speed from the latest over-time buckets
    const data = overTime;
    if (!data.length) return { upload_bps: 0, download_bps: 0 };
    const last = data[data.length - 1];
    return {
      upload_bps: (last.upload || 0) / 30,
      download_bps: (last.download || 0) / 30,
    };
  }, [overTime]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [timeResp, svcResp] = await Promise.all([
          api.getTrafficOverTime(30, 6),
          api.getTopServices(5),
        ]);
        if (!cancelled) {
          setOverTime(timeResp.data);
          setServices(svcResp.data);
        }
      } catch {
        /* charts remain empty on failure */
      } finally {
        if (!cancelled) setLoadingChart(false);
      }
    };
    load();
    const id = setInterval(load, 10000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const handleToggle = async () => {
    setBusy(true);
    try {
      if (monitoring?.running) await stopMonitoring();
      else await startMonitoring(monitoring?.demo_mode ? "demo" : "live");
    } catch (err) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Network Privacy</h1>
          <p className="page-sub">
            Real-time visibility into what your device communicates with, how much data is
            transmitted, and whether communication is encrypted.
          </p>
        </div>
        <div className="monitor-controls">
          <div className="monitor-badge">
            <span className="dot" />{" "}
            {monitoring?.running ? "Monitoring: ACTIVE" : "Monitoring: STOPPED"}
            <span className="monitor-interface">
              {monitoring?.interface ? ` · ${monitoring.interface}` : ""}
              {monitoring?.mode === "demo" ? " · DEMO" : ""}
            </span>
            <span className={`monitor-interface status-chip ${connectionStatus === "LIVE" ? "status-live" : connectionStatus === "POLLING" ? "status-polling" : "status-reconnecting"}`}>
              {connectionStatus === "LIVE" ? "● LIVE" : connectionStatus === "POLLING" ? "● POLLING" : "● RECONNECTING"}
            </span>
          </div>
          {monitoring?.running ? (
            <button className="btn btn-danger" onClick={handleToggle} disabled={busy}>
              Stop Monitoring
            </button>
          ) : (
            <button className="btn btn-primary" onClick={handleToggle} disabled={busy}>
              Start Monitoring
            </button>
          )}
        </div>
      </div>

      {demo && (
        <div className="demo-banner">
          <strong>DEMO MODE</strong> — displaying clearly labeled synthetic traffic. Live packet
          capture is not active. This data is not real network traffic.
        </div>
      )}

      <div className="metric-grid">
        <MetricCard
          title="Privacy Score"
          value={`${privacyScore?.score ?? 0}/100`}
          sub="Application-defined score"
          icon="🛡️"
          tone="accent"
        />
        <MetricCard
          title="Encrypted Traffic"
          value={`${encryptedPct.toFixed(1)}%`}
          sub="Observable encryption"
          icon="🔒"
          tone="good"
        />
        <MetricCard
          title="Unencrypted Traffic"
          value={`${(100 - encryptedPct).toFixed(1)}%`}
          sub="Potential privacy exposure"
          icon="⚠️"
          tone="warn"
        />
        <MetricCard
          title="Uploaded"
          value={formatBytes(summary?.bytes_sent ?? 0)}
          sub={speeds.upload_bps ? `≈ ${formatBytes(speeds.upload_bps)}/s` : "Idle"}
          icon="⬆️"
        />
        <MetricCard
          title="Downloaded"
          value={formatBytes(summary?.bytes_received ?? 0)}
          sub={speeds.download_bps ? `≈ ${formatBytes(speeds.download_bps)}/s` : "Idle"}
          icon="⬇️"
        />
        <MetricCard
          title="Active Connections"
          value={summary?.active_connections ?? 0}
          sub={`${summary?.total_connections ?? 0} total connections`}
          icon="🔗"
        />
      </div>

      <div className="grid-2">
        <TrafficChart data={overTime} loading={loadingChart} />
        <TrafficUsage summary={summary} speeds={speeds} />
      </div>

      <div className="grid-2">
        <PrivacyScore scoreData={privacyScore} />
        <EncryptionChart
          encrypted={encryptedPct}
          unencrypted={100 - encryptedPct}
        />
      </div>

      <div className="grid-2">
        <TrafficChart data={overTime} loading={loadingChart} />
        <TrafficUsage summary={summary} speeds={speeds} />
      </div>

      <div className="grid-2">
        <ServiceList services={services} />
        <WebsiteList websites={websites} />
      </div>

      <div className="grid-2">
        <ConnectionTable connections={activeConnections} />
        <AlertPanel alerts={alerts} />
      </div>

      <div className="panel">
        <div className="panel-head">
          <div className="card-title">About Privacy by Design</div>
        </div>
        <p className="privacy-note">
          This application analyzes network <strong>metadata</strong> for privacy visibility. It
          does <strong>not</strong> decrypt, store, or transmit private communication content —
          no passwords, messages, cookies, file contents, or authentication tokens are collected.
        </p>
        <p className="privacy-note">
          Website and domain labels come from <strong>reliable, observable metadata only</strong>:
          the TLS SNI hostname or a recent DNS mapping. Applications are never guessed from a
          domain or port, and DNS mappings expire quickly so traffic is never attributed to the
          wrong site after an IP changes hands.
        </p>
        <p className="privacy-note">
          Privacy scores are an application-defined estimate based on observable encryption and
          protocol metadata, not an industry-standard security measurement.
        </p>
      </div>
    </div>
  );
}