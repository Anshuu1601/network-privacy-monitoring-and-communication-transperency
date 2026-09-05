import axios from "axios";

const api = axios.create({
  baseURL: "",
  timeout: 15000,
});

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const message =
      error.response?.data?.detail || error.message || "Something went wrong";
    return Promise.reject(new Error(message));
  }
);

export const getHealth = () => api.get("/api/health");
export const getInterfaces = () => api.get("/api/interfaces");
export const getCaptureStatus = () => api.get("/api/capture/status");
export const startCapture = (mode = "live") =>
  api.post("/api/capture/start", { mode });
export const stopCapture = () => api.post("/api/capture/stop");
export const selectInterface = (iface) =>
  api.post("/api/capture/interface", { interface: iface });

export const getLiveTraffic = () => api.get("/api/traffic/live");
export const getTrafficSummary = () => api.get("/api/traffic/summary");
export const getTrafficHistory = (limit = 300) =>
  api.get("/api/traffic/history", { params: { limit } });
export const getTrafficOverTime = (bucket = 30, hours = 6) =>
  api.get("/api/traffic/over-time", { params: { bucket, hours } });

export const getDevices = () => api.get("/api/devices");
export const getDevice = (id) => api.get(`/api/devices/${id}`);
export const getDeviceTraffic = (id, limit = 200) =>
  api.get(`/api/devices/${id}/traffic`, { params: { limit } });

export const getPrivacyScore = () => api.get("/api/privacy/score");
export const getPrivacyEncryption = () => api.get("/api/privacy/encryption");
export const getPrivacySummary = () => api.get("/api/privacy/summary");

export const getServices = () => api.get("/api/services");
export const getTopServices = (limit = 5) =>
  api.get("/api/services/top", { params: { limit } });

export const getWebsites = (limit = 10) =>
  api.get("/api/websites", { params: { limit } });
export const getTopWebsites = (limit = 5) =>
  api.get("/api/websites/top", { params: { limit } });
export const getDnsDomains = (limit = 100) =>
  api.get("/api/dns/domains", { params: { limit } });

export const getAlerts = (limit = 50) => api.get("/api/alerts", { params: { limit } });
export const getUnencryptedAlerts = (limit = 50) =>
  api.get("/api/alerts/unencrypted", { params: { limit } });

export const getDailyReport = () => api.get("/api/reports/daily");
export const getWeeklyReport = () => api.get("/api/reports/weekly");
export const getCustomReport = (start, end) =>
  api.get("/api/reports/custom", { params: { start, end } });

export const downloadCsv = () =>
  api.get("/api/reports/export/csv", { responseType: "blob" });
export const downloadPdf = (reportType = "daily", start = null, end = null) =>
  api.get("/api/reports/export/pdf", {
    params: { report_type: reportType, start, end },
    responseType: "blob",
  });

export const getSettings = () => api.get("/api/settings");
export const updateScoreWeights = (weights) =>
  api.post("/api/settings/score-weights", weights);
export const setDemoMode = (enabled) => api.post("/api/settings/demo", { enabled });
export const setRetention = (days) => api.post("/api/settings/retention", { days });
export const clearOldData = (days) =>
  api.post("/api/settings/retention/clear", null, { params: { days } });
