import React, { useEffect, useState } from "react";
import { useLiveContext } from "../context/LiveContext";
import * as api from "../services/api";

function SettingSection({ title, children }) {
  return (
    <div className="panel settings-section">
      <div className="panel-head">
        <div className="card-title">{title}</div>
      </div>
      {children}
    </div>
  );
}

export default function Settings() {
  const { monitoring, demo, startMonitoring, stopMonitoring, refresh } = useLiveContext();
  const [interfaces, setInterfaces] = useState([]);
  const [settings, setSettings] = useState(null);
  const [selectedInterface, setSelectedInterface] = useState("");
  const [weights, setWeights] = useState({ encryption: 60, protocol: 20, unencrypted_penalty: 20 });
  const [retention, setRetention] = useState(30);
  const [notify, setNotify] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [ifaces, cfg] = await Promise.all([api.getInterfaces(), api.getSettings()]);
        if (!cancelled) {
          setInterfaces(ifaces.data);
          setSettings(cfg.data);
          setSelectedInterface(ifaces.data[0]?.name || "");
          setWeights(cfg.data.score_weights);
          setRetention(cfg.data.retention_days);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const flash = (msg) => {
    setNotify(msg);
    setTimeout(() => setNotify(null), 3000);
  };

  const handleStart = async (mode) => {
    setBusy(true);
    setError(null);
    try {
      if (mode === "demo") await api.setDemoMode(true);
      else {
        await api.setDemoMode(false);
        if (selectedInterface) await api.selectInterface(selectedInterface);
      }
      await startMonitoring(mode);
      flash(`${mode === "demo" ? "Demo" : "Live"} monitoring started.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleStop = async () => {
    setBusy(true);
    try {
      await stopMonitoring();
      flash("Monitoring stopped.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const saveWeights = async () => {
    setError(null);
    try {
      const resp = await api.updateScoreWeights(weights);
      flash("Privacy score weights saved.");
      return resp.data;
    } catch (err) {
      setError(err.message);
    }
  };

  const saveRetention = async () => {
    setError(null);
    try {
      await api.setRetention(retention);
      flash("Retention period saved.");
    } catch (err) {
      setError(err.message);
    }
  };

  const clearOldData = async () => {
    if (!retention || retention <= 0) {
      setError("Unlimited retention is set. Specify a day count to clear old data.");
      return;
    }
    const confirmed = window.confirm(
      `This will permanently delete connection history older than ${retention} days. Continue?`
    );
    if (!confirmed) return;
    setError(null);
    try {
      const resp = await api.clearOldData(retention);
      flash(`Deleted ${resp.data.deleted} old connection records.`);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  };

  const applyWeightsToScore = () => {
    const total = weights.encryption + weights.protocol + weights.unencrypted_penalty;
    return total > 0 ? total : 1;
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Settings</h1>
          <p className="page-sub">
            Configure packet capture, privacy score weighting, alert and data retention options.
          </p>
        </div>
      </div>

      {notify && <div className="success-banner">✓ {notify}</div>}
      {error && <div className="error-banner">⚠ {error}</div>}

      <div className="settings-grid">
        <SettingSection title="Monitoring Control">
          <div className="settings-row">
            <div className="settings-label">
              <strong>Current status</strong>
              <span>
                {monitoring?.running ? "Monitoring: ACTIVE" : "Monitoring: STOPPED"} ·{" "}
                {monitoring?.mode?.toUpperCase() || "LIVE"}
                {monitoring?.interface ? ` · ${monitoring.interface}` : ""}
              </span>
            </div>
            <div className="settings-actions">
              <button
                className="btn btn-primary"
                onClick={() => handleStart("live")}
                disabled={busy || monitoring?.running}
              >
                Start Monitoring
              </button>
              <button
                className="btn btn-danger"
                onClick={handleStop}
                disabled={busy || !monitoring?.running}
              >
                Stop Monitoring
              </button>
            </div>
          </div>
          <p className="privacy-note">
            Live capture requires appropriate packet-capture permissions on your device. If
            permission is unavailable, use Demo Mode for the presentation.
          </p>
        </SettingSection>

        <SettingSection title="Network Interface">
          <div className="settings-row">
            <div className="settings-label">
              <strong>Select capture interface</strong>
              <span>Interface used for packet capture. Leave the default for auto-detection.</span>
            </div>
            <select
              className="input select"
              value={selectedInterface}
              onChange={(e) => setSelectedInterface(e.target.value)}
            >
              {interfaces.map((iface) => (
                <option key={iface.name} value={iface.name}>
                  {iface.name} {iface.ip ? `(${iface.ip})` : ""}
                </option>
              ))}
            </select>
          </div>
          <div className="settings-row">
            <div className="settings-label">
              <strong>Demo Mode</strong>
              <span>Generate clearly labeled synthetic traffic when live capture is unavailable.</span>
            </div>
            <button
              className="btn btn-ghost"
              onClick={() => handleStart("demo")}
              disabled={busy || (monitoring?.running && demo)}
            >
              Start Demo Mode
            </button>
          </div>
        </SettingSection>

        <SettingSection title="Privacy Score Weights">
          <div className="settings-row">
            <div className="settings-label">
              <strong>Weight configuration</strong>
              <span>
                Weighted factors determine the application-defined privacy score. Current total:{" "}
                {applyWeightsToScore()}%
              </span>
            </div>
            <div className="weight-inputs">
              <label className="weight-field">
                Encryption contribution
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="input"
                  value={weights.encryption}
                  onChange={(e) =>
                    setWeights({ ...weights, encryption: Number(e.target.value) })
                  }
                />
              </label>
              <label className="weight-field">
                Protocol contribution
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="input"
                  value={weights.protocol}
                  onChange={(e) =>
                    setWeights({ ...weights, protocol: Number(e.target.value) })
                  }
                />
              </label>
              <label className="weight-field">
                Unencrypted penalty
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="input"
                  value={weights.unencrypted_penalty}
                  onChange={(e) =>
                    setWeights({ ...weights, unencrypted_penalty: Number(e.target.value) })
                  }
                />
              </label>
            </div>
            <button className="btn btn-primary" onClick={saveWeights}>
              Save Weights
            </button>
          </div>
          <p className="privacy-note">
            The privacy score is a transparent, application-defined estimate based on observable
            metadata. It is not an industry-standard security measurement.
          </p>
        </SettingSection>

        <SettingSection title="Data Retention">
          <div className="settings-row">
            <div className="settings-label">
              <strong>Retention period</strong>
              <span>How long connection history is kept before it can be cleared.</span>
            </div>
            <select
              className="input select"
              value={retention}
              onChange={(e) => setRetention(Number(e.target.value))}
            >
              <option value={7}>7 days</option>
              <option value={30}>30 days</option>
              <option value={90}>90 days</option>
              <option value={0}>Unlimited</option>
            </select>
          </div>
          <div className="settings-actions">
            <button className="btn btn-ghost" onClick={saveRetention}>
              Save Retention
            </button>
            <button className="btn btn-danger" onClick={clearOldData}>
              Clear Old Data
            </button>
          </div>
          <p className="privacy-note">
            Data is never deleted without explicit confirmation. Only network metadata is stored —
            never packet payloads or private communication content.
          </p>
        </SettingSection>
      </div>
    </div>
  );
}