import React, { useEffect, useState } from "react";
import DeviceList from "../components/DeviceList";
import MetricCard from "../components/MetricCard";
import { useLiveContext } from "../context/LiveContext";
import * as api from "../services/api";
import { formatBytes } from "../utils";

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { summary } = useLiveContext();

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const resp = await api.getDevices();
        if (!cancelled) setDevices(resp.data);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const totalUp = devices.reduce((acc, d) => acc + (d.bytes_sent || 0), 0);
  const totalDown = devices.reduce((acc, d) => acc + (d.bytes_received || 0), 0);
  const totalActive = devices.reduce((acc, d) => acc + (d.active_connections || 0), 0);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Devices</h1>
          <p className="page-sub">
            Monitoring device information, encryption percentage and data usage. The architecture
            supports multiple devices on a local network.
          </p>
        </div>
      </div>

      <div className="metric-grid">
        <MetricCard title="Devices Monitored" value={devices.length} icon="💻" />
        <MetricCard title="Total Uploaded" value={formatBytes(totalUp)} icon="⬆️" />
        <MetricCard title="Total Downloaded" value={formatBytes(totalDown)} icon="⬇️" />
        <MetricCard
          title="Active Connections"
          value={totalActive}
          sub={`${summary?.total_connections ?? 0} total`}
          icon="🔗"
        />
      </div>

      {loading && <div className="panel"><div className="chart-empty">Loading devices…</div></div>}
      {error && <div className="error-banner">⚠ {error}</div>}
      {!loading && !error && <DeviceList devices={devices} />}
    </div>
  );
}