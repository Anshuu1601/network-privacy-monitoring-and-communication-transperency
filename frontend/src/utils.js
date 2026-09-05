export function formatBytes(bytes, decimals = 1) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB", "PB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

export function formatSpeed(bytesPerSecond) {
  if (!bytesPerSecond) return "0 B/s";
  return `${formatBytes(bytesPerSecond)}/s`;
}

function toDate(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

/**
 * Convert a UTC ISO-8601 timestamp to the user's LOCAL timezone and render
 * date + time. The backend always sends UTC (`...Z`); `Date` parses that as an
 * instant and `toLocale*` renders it in the browser/system timezone. Local
 * timezone is never hard-coded.
 */
export function formatLocalDateTime(iso) {
  const d = toDate(iso);
  if (!d) return iso || "—";
  return d.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatLocalTime(iso) {
  const d = toDate(iso);
  if (!d) return iso || "—";
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatLocalDate(iso) {
  const d = toDate(iso);
  if (!d) return iso || "—";
  return d.toLocaleDateString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatLocalTimeHourMinute(iso) {
  const d = toDate(iso);
  if (!d) return "";
  return `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
}

export function formatTime(iso) {
  return formatLocalTime(iso);
}

export function formatDate(iso) {
  return formatLocalDate(iso);
}

export function formatLocalDateIso(iso) {
  const d = toDate(iso);
  if (!d) return "";
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/**
 * Human-friendly flow duration.
 *
 *   active && < 1s  -> "Live"
 *   < 1s             -> "0.8 sec"
 *   < 60s            -> "12 sec"
 *   < 1h             -> "1 min 24 sec"
 *   otherwise        -> "1 hr 5 min"
 *
 * `active` marks a currently-running connection: it shows "Live" instead of a
 * blank dash and appends "(active)" to non-trivial durations.
 */
export function formatDuration(seconds, { active = false } = {}) {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) {
    return active ? "Live" : "—";
  }
  const s = Math.max(0, Number(seconds));
  if (active && s < 1) return "Live";
  let base;
  if (s < 1) {
    base = `${s.toFixed(1)} sec`;
  } else if (s < 60) {
    base = Number.isInteger(s) ? `${s} sec` : `${s.toFixed(1)} sec`;
  } else if (s < 3600) {
    const m = Math.floor(s / 60);
    const sec = Math.round(s % 60);
    base = sec ? `${m} min ${sec} sec` : `${m} min`;
  } else {
    const h = Math.floor(s / 3600);
    const m = Math.round((s % 3600) / 60);
    base = m ? `${h} hr ${m} min` : `${h} hr`;
  }
  return active ? `${base} (active)` : base;
}

export function encryptionLabelShort(encrypted) {
  return encrypted ? "Encrypted" : "Unencrypted";
}

export function nowIso() {
  return new Date().toISOString();
}

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}