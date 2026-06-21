import test from "node:test";
import assert from "node:assert/strict";

import {
  PROFILE_SCHEMA,
  createDemoPayload,
  filterRules,
  formatScheduler,
  parsePayloadText,
} from "../library.mjs";

test("demo payload stays schema-valid and preserves umlauts", () => {
  const payload = createDemoPayload();
  assert.equal(payload.schema, PROFILE_SCHEMA);
  assert.equal(payload.accounts[0].name, "Büro Köln");
  assert.equal(payload.rules[0].name, "Newsletter älter als 90 Tage");
  assert.deepEqual(payload.settings.selected_rule_folders, ["INBOX", "Newsletters"]);
});

test("parser normalizes legacy alias rule keys", () => {
  const payload = parsePayloadText(JSON.stringify({
    schema: PROFILE_SCHEMA,
    app: "UniversalMailCleaner",
    exported_at: "2026-06-22T01:30:00+02:00",
    accounts: [
      { name: "Archiv", protocol: "IMAP", host: "imap.example.org", user: "mail@example.org" },
    ],
    rules: [
      {
        name: "Große Mails",
        account: "Archiv",
        type: "size_mb",
        size_mb: 25,
        active: false,
      },
    ],
    settings: {
      selected_rule_folders: ["Archiv", "INBOX"],
      scheduler: { enabled: true, interval_hours: 12, run_on_startup: true },
    },
  }));

  assert.equal(payload.rules[0].target_account, "Archiv");
  assert.equal(payload.rules[0].filter_type, "size_mb");
  assert.equal(payload.rules[0].value, "25");
  assert.equal(payload.rules[0].active, false);
  assert.equal(formatScheduler(payload.settings), "Every 12h, startup on");
});

test("rule filtering supports search and active-state filtering", () => {
  const payload = createDemoPayload();
  assert.equal(filterRules(payload.rules, "reise", "all").length, 1);
  assert.equal(filterRules(payload.rules, "", "active").length, 1);
  assert.equal(filterRules(payload.rules, "", "inactive").length, 1);
});

test("parser rejects unsupported schemas", () => {
  assert.throws(
    () => parsePayloadText(JSON.stringify({ schema: "wrong-schema" })),
    /Unsupported profile schema/,
  );
});
