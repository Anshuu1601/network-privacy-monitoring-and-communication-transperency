import React, { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import * as api from "../services/api";
import { downloadBlob, formatBytes, formatLocalDateTime } from "../utils";

function ReportView({ report, loading }) {
  if (loading) return <div className="chart-empty">Generating report…</div>;
  if (!report) return <div className="chart-empty">Select a report to view.</div>;

  const score = report.privacy_score || {};
  const daily = report.daily_traffic || [];

  return (
    <div className="report-view">
      <div className="report-header">
        <div className="report-type">{report.report_type?.toUpperCase()} REPORT</div>
        <div className="report-period">{report.period_label}</div>
        <div className="report-tz">
          Timezone: {report.timezone || "UTC"} — times shown in your browser's local timezone
        </div>
      </div>

      <div className="report-metrics">
        <div className="report-metric">
          <span>Total Connections</span>
          <strong>{report.total_connections}</strong>
        </div>
        <div className="report-metric">
          <span>Encrypted</span>
          <strong>{report.encrypted_connections}</strong>
        </div>
        <div className="report-metric">
          <span>Unencrypted</span>
          <strong>{report.unencrypted_connections}</strong>
        </div>
        <div className="report-metric">
          <span>Privacy Score</span>
          <strong>{score.score}/100</strong>
        </div>
        <div className="report-metric">
          <span>Upload</span>
          <strong>{formatBytes(report.bytes_sent)}</strong>
        </div>
        <div className="report-metric">
          <span>Download</span>
          <strong>{formatBytes(report.bytes_received)}</strong>
        </div>
      </div>

      {score.reasons?.length > 0 && (
        <div className="score-reasons">
          {score.reasons.map((r, i) => (
            <div key={i} className={`score-reason ${r.startsWith("+") ? "good" : "bad"}`}>
              {r}
            </div>
          ))}
        </div>
      )}

      {report.report_type === "weekly" && daily.length > 0 && (
        <div className="report-chart">
          <div className="card-title">Daily Traffic</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={daily} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="date" stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis
                tickFormatter={(v) => formatBytes(v)}
                stroke="var(--muted)"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={56}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value, name) => [
                  name === "bytes_sent" ? formatBytes(value) : value,
                  name === "bytes_sent" ? "Upload" : name,
                ]}
              />
              <Bar dataKey="bytes_sent" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="bytes_received" fill="#22c55e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {report.services?.length > 0 && (
        <div className="report-section">
          <div className="card-title">Top Services</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Service</th>
                <th>Connections</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {report.services.map((s, i) => (
                <tr key={i}>
                  <td className="cell-service">{s.service}</td>
                  <td>{s.count}</td>
                  <td>{formatBytes(s.bytes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="report-section">
        <div className="card-title">Privacy Alerts</div>
        {report.alerts?.length ? (
          <ul className="alert-list">
            {report.alerts.map((a, i) => (
              <li key={i} className="alert-item">
                <div className="alert-line">
                  <span className="badge badge-alert">{a.severity}</span>
                  <span className="alert-time">{formatLocalDateTime(a.timestamp)}</span>
                </div>
                <div className="alert-msg">{a.message}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="privacy-note">No unencrypted communication events recorded.</p>
        )}
      </div>
    </div>
  );
}

export default function Reports() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reportType, setReportType] = useState("daily");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [exportBusy, setExportBusy] = useState(false);

  const loadReport = async (type, start = null, end = null) => {
    setLoading(true);
    setError(null);
    try {
      let resp;
      if (type === "daily") resp = await api.getDailyReport();
      else if (type === "weekly") resp = await api.getWeeklyReport();
      else resp = await api.getCustomReport(start, end);
      setReport(resp.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = () => {
    if (reportType === "custom") {
      if (!startDate || !endDate) {
        setError("Please select both start and end dates.");
        return;
      }
      loadReport("custom", startDate, endDate);
    } else {
      loadReport(reportType);
    }
  };

  const handleExport = async (format) => {
    setExportBusy(true);
    setError(null);
    try {
      let blob;
      if (format === "csv") {
        blob = (await api.downloadCsv()).data;
        downloadBlob(blob, "connection_history.csv");
      } else {
        let params = { reportType };
        if (reportType === "custom") {
          if (!startDate || !endDate) {
            setError("Select both start and end dates before exporting.");
            setExportBusy(false);
            return;
          }
          params = { reportType, start: startDate, end: endDate };
        }
        blob = (await api.downloadPdf(params.reportType, params.start, params.end)).data;
        downloadBlob(blob, `${params.reportType}_report.pdf`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setExportBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Privacy Reports</h1>
          <p className="page-sub">
            Generate daily, weekly or custom reports and export connection history as CSV or
            professional PDF documents.
          </p>
        </div>
      </div>

      <div className="report-controls">
        <select
          className="input select"
          value={reportType}
          onChange={(e) => setReportType(e.target.value)}
        >
          <option value="daily">Today's Report</option>
          <option value="weekly">Weekly Report</option>
          <option value="custom">Custom Date Range</option>
        </select>

        {reportType === "custom" && (
          <>
            <input
              type="date"
              className="input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <span className="range-sep">to</span>
            <input
              type="date"
              className="input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </>
        )}

        <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating…" : "Generate Report"}
        </button>

        <div className="export-buttons">
          <button
            className="btn btn-ghost"
            onClick={() => handleExport("csv")}
            disabled={exportBusy}
          >
            Export CSV
          </button>
          <button
            className="btn btn-ghost"
            onClick={() => handleExport("pdf")}
            disabled={exportBusy}
          >
            Export PDF
          </button>
        </div>
      </div>

      {error && <div className="error-banner">⚠ {error}</div>}

      <div className="panel">
        <ReportView report={report} loading={loading} />
      </div>
    </div>
  );
}