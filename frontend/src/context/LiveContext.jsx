import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import * as api from "../services/api";

const LiveContext = createContext(null);

export function useLiveContext() {
  return useContext(LiveContext);
}

function emptyLive() {
  return {
    summary: {
      total_connections: 0,
      encrypted_connections: 0,
      unencrypted_connections: 0,
      bytes_sent: 0,
      bytes_received: 0,
      active_connections: 0,
      encrypted_percentage: 0,
    },
    privacy_score: {
      score: 0,
      encrypted_percentage: 0,
      unencrypted_percentage: 0,
      reasons: [],
      weights: {},
    },
    active_connections: [],
    alerts: [],
    websites: [],
    monitoring: { running: false, mode: "live", interface: "", demo_mode: false },
    demo_data: false,
    timestamp: null,
  };
}

function connectionKey(c) {
  return [
    c.source_ip,
    c.destination_ip,
    c.source_port,
    c.destination_port,
    c.protocol,
  ].join("|");
}

function upsertConnection(list, next) {
  const key = connectionKey(next);
  const idx = list.findIndex((c) => connectionKey(c) === key);
  if (idx === -1) return [next, ...list];
  const copy = list.slice();
  copy[idx] = { ...copy[idx], ...next };
  return copy;
}

function removeConnection(list, gone) {
  const key = connectionKey(gone);
  return list.filter((c) => connectionKey(c) !== key);
}

export function LiveProvider({ children }) {
  const [live, setLive] = useState(emptyLive);
  const [activeConnections, setActiveConnections] = useState([]);
  const [websites, setWebsites] = useState([]);
  const [connected, setConnected] = useState(false);
  const [usingWs, setUsingWs] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("POLLING");
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const pollTimer = useRef(null);
  const reconnectDelay = useRef(2000);

  const applyLivePayload = useCallback((payload) => {
    if (!payload) return;
    setLive((prev) => ({ ...prev, ...payload }));
    if (payload.active_connections) setActiveConnections(payload.active_connections);
    if (payload.websites) setWebsites(payload.websites);
  }, []);

  const applyTrafficUpdate = useCallback((conn) => {
    if (!conn) return;
    setActiveConnections((prev) => upsertConnection(prev, conn));
  }, []);

  const applyConnectionClosed = useCallback((conn) => {
    if (!conn) return;
    setActiveConnections((prev) => removeConnection(prev, conn));
  }, []);

  const applyAlert = useCallback((alert) => {
    if (!alert) return;
    setLive((prev) => ({
      ...prev,
      alerts: [alert, ...(prev.alerts || [])].slice(0, 10),
    }));
  }, []);

  const applyMonitoringStatus = useCallback((monitoring) => {
    if (!monitoring) return;
    setLive((prev) => ({ ...prev, monitoring }));
  }, []);

  const handleMessage = useCallback(
    (msg) => {
      if (!msg || !msg.type) return;
      switch (msg.type) {
        case "live":
          applyLivePayload(msg);
          break;
        case "traffic_update":
          applyTrafficUpdate(msg.connection);
          break;
        case "connection_closed":
          applyConnectionClosed(msg.connection);
          break;
        case "alert":
          applyAlert(msg.alert);
          break;
        case "monitoring_status":
          applyMonitoringStatus(msg.monitoring);
          break;
        default:
          break;
      }
    },
    [applyLivePayload, applyTrafficUpdate, applyConnectionClosed, applyAlert, applyMonitoringStatus]
  );

  // WebSocket connection with reconnect + polling fallback
  useEffect(() => {
    let stopped = false;

    const wsUrl = () => {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      return `${proto}://${window.location.host}/ws/traffic`;
    };

    const stopPolling = () => {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
        pollTimer.current = null;
      }
    };

    const startPolling = () => {
      setConnectionStatus("POLLING");
      if (pollTimer.current) return;
      const tick = async () => {
        try {
          const resp = await api.getLiveTraffic();
          handleMessage(resp.data);
          setConnected(true);
          setError(null);
        } catch (err) {
          setError(err.message);
          setConnected(false);
        }
      };
      tick();
      pollTimer.current = setInterval(tick, 3000);
    };

    const connectWs = () => {
      if (stopped) return;
      try {
        const ws = new WebSocket(wsUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          if (stopped) return;
          setUsingWs(true);
          setConnected(true);
          setConnectionStatus("LIVE");
          setError(null);
          reconnectDelay.current = 2000;
          stopPolling();
        };

        ws.onmessage = (event) => {
          try {
            handleMessage(JSON.parse(event.data));
          } catch {
            /* ignore malformed */
          }
        };

        ws.onerror = () => {
          if (stopped) return;
          setUsingWs(false);
          setConnected(false);
          setConnectionStatus("RECONNECTING");
          startPolling();
        };

        ws.onclose = () => {
          if (stopped) return;
          setUsingWs(false);
          setConnected(false);
          setConnectionStatus("RECONNECTING");
          startPolling();
          const delay = reconnectDelay.current;
          reconnectDelay.current = Math.min(delay * 2, 30000);
          setTimeout(connectWs, delay);
        };
      } catch {
        setConnectionStatus("POLLING");
        startPolling();
      }
    };

    connectWs();

    return () => {
      stopped = true;
      stopPolling();
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          /* noop */
        }
      }
    };
  }, [handleMessage]);

  const refresh = useCallback(async () => {
    try {
      const resp = await api.getLiveTraffic();
      handleMessage(resp.data);
    } catch (err) {
      setError(err.message);
    }
  }, [handleMessage]);

  const startMonitoring = useCallback(
    async (mode = "live") => {
      const resp = await api.startCapture(mode);
      await refresh();
      return resp.data;
    },
    [refresh]
  );

  const stopMonitoring = useCallback(async () => {
    const resp = await api.stopCapture();
    await refresh();
    return resp.data;
  }, [refresh]);

  const value = {
    live,
    connected,
    usingWs,
    connectionStatus,
    error,
    refresh,
    startMonitoring,
    stopMonitoring,
    monitoring: live.monitoring,
    demo: live.demo_data,
    summary: live.summary,
    privacyScore: live.privacy_score,
    activeConnections,
    alerts: live.alerts,
    websites,
  };

  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>;
}