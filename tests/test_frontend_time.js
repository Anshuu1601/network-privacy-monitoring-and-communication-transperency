// Frontend local-timezone conversion tests.
//
// The backend always sends UTC ISO-8601 timestamps ("2026-08-19T17:31:41.123Z").
// The frontend converts that instant to the user's local timezone exactly once
// via the shared utilities in frontend/src/utils.js. These tests pin that
// behavior. They use the process timezone, so run with a fixed TZ, e.g.:
//
//   TZ=Asia/Dhaka node tests/test_frontend_time.js
//
// (Node.js 18+ required.)
import { strict as assert } from "node:assert";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const utils = require("../frontend/src/utils.js");

const UTC_INSTANT = "2026-08-19T17:31:41.123Z";
// 2026-08-19T17:31:41Z == 23:31:41 in Asia/Dhaka (+06:00)
const LOCAL_TZ = process.env.TZ || Intl.DateTimeFormat().resolvedOptions().timeZone;
const LOCAL_TIME = new Date(UTC_INSTANT).toLocaleTimeString([], {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});

function test(name, fn) {
  try {
    fn();
    console.log(`PASS ${name}`);
  } catch (err) {
    console.error(`FAIL ${name}`);
    throw err;
  }
}

test("formatLocalTime renders UTC instant in local timezone", () => {
  assert.equal(utils.formatLocalTime(UTC_INSTANT), LOCAL_TIME);
  // Sanity: the local time is NOT the raw UTC string.
  assert.notEqual(LOCAL_TIME.replace(/\s/g, ""), "17:31:41");
});

test("formatLocalDateTime includes date and local time", () => {
  const d = new Date(UTC_INSTANT);
  const expected = d.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  assert.equal(utils.formatLocalDateTime(UTC_INSTANT), expected);
});

test("formatDuration formats sub-second / seconds / minutes", () => {
  assert.equal(utils.formatDuration(0.8), "0.8 sec");
  assert.equal(utils.formatDuration(2.4), "2.4 sec");
  assert.equal(utils.formatDuration(12), "12 sec");
  assert.equal(utils.formatDuration(84), "1 min 24 sec");
});

test("formatDuration handles active flows", () => {
  assert.equal(utils.formatDuration(0.5, { active: true }), "Live");
  assert.equal(utils.formatDuration(12, { active: true }), "12 sec (active)");
  assert.equal(utils.formatDuration(undefined, { active: true }), "Live");
});

test("formatDuration does not render a dash when duration is known", () => {
  assert.notEqual(utils.formatDuration(1.0), "—");
});

test("formatLocalDateIso returns local calendar date", () => {
  // With TZ Asia/Dhaka the UTC 17:31 of Aug 19 is still Aug 19 locally.
  const local = new Date(UTC_INSTANT);
  const expected = `${local.getFullYear()}-${String(local.getMonth() + 1).padStart(2, "0")}-${String(local.getDate()).padStart(2, "0")}`;
  assert.equal(utils.formatLocalDateIso(UTC_INSTANT), expected);
});

test("missing timestamp renders dash", () => {
  assert.equal(utils.formatLocalTime(null), "—");
  assert.equal(utils.formatLocalDateTime(undefined), "—");
});

console.log(`\nAll frontend time tests passed (TZ=${LOCAL_TZ}).`);