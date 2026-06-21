export const PROFILE_SCHEMA = "universalmailcleaner-profile-v1";
export const STORAGE_KEY = "umc.web_companion.payload";

const DEFAULT_SETTINGS = {
  safe_mode: true,
  selected_rule_folders: ["INBOX"],
  large_item_threshold_mb: 10,
  scan_mail: true,
  scan_drive: false,
  scheduler: {
    enabled: false,
    interval_hours: 24,
    run_on_startup: false,
    last_run: "",
    next_run: "",
  },
};

function asObject(value, message) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(message);
  }
  return value;
}

function normalizeText(value, fallback = "") {
  return typeof value === "string" ? value.trim() : fallback;
}

function normalizeBoolean(value, fallback = false) {
  return typeof value === "boolean" ? value : fallback;
}

function normalizeInteger(value, fallback = 0) {
  const numeric = Number.parseInt(value, 10);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

function normalizeFolders(value) {
  const folders = normalizeArray(value)
    .map((folder) => normalizeText(folder))
    .filter(Boolean);
  return folders.length > 0 ? folders : ["INBOX"];
}

export function normalizeAccount(account, index = 0) {
  const source = asObject(account, `Account #${index + 1} is not an object.`);
  const name = normalizeText(source.name, `Account ${index + 1}`);
  const protocol = normalizeText(source.protocol, "IMAP");
  const host = normalizeText(source.host);
  const port = normalizeInteger(source.port, protocol === "Gmail API" ? 0 : 993);
  const user = normalizeText(source.user);
  const trashFolder = normalizeText(source.trash_folder);

  return {
    name,
    protocol,
    host,
    port,
    user,
    trash_folder: trashFolder,
  };
}

function normalizeRuleValue(rule, filterType) {
  if (rule.value !== undefined && rule.value !== null && String(rule.value).trim() !== "") {
    return String(rule.value).trim();
  }
  if (filterType === "older_than_days" && rule.older_than_days !== undefined) {
    return String(rule.older_than_days).trim();
  }
  if (filterType === "size_mb" && rule.size_mb !== undefined) {
    return String(rule.size_mb).trim();
  }
  return "";
}

export function normalizeRule(rule, index = 0) {
  const source = asObject(rule, `Rule #${index + 1} is not an object.`);
  const filterType = normalizeText(source.filter_type || source.type);
  const value = normalizeRuleValue(source, filterType);

  if (!filterType || !value) {
    throw new Error(`Rule #${index + 1} is incomplete.`);
  }

  return {
    name: normalizeText(source.name, `Rule ${index + 1}`),
    target_account: normalizeText(source.target_account || source.account, "All"),
    filter_type: filterType,
    value,
    active: normalizeBoolean(source.active, true),
  };
}

export function normalizeSettings(rawSettings) {
  const source = rawSettings && typeof rawSettings === "object" && !Array.isArray(rawSettings)
    ? rawSettings
    : {};
  const schedulerSource =
    source.scheduler && typeof source.scheduler === "object" && !Array.isArray(source.scheduler)
      ? source.scheduler
      : {};

  return {
    safe_mode: normalizeBoolean(source.safe_mode, DEFAULT_SETTINGS.safe_mode),
    selected_rule_folders: normalizeFolders(source.selected_rule_folders),
    large_item_threshold_mb: normalizeInteger(
      source.large_item_threshold_mb,
      DEFAULT_SETTINGS.large_item_threshold_mb,
    ),
    scan_mail: normalizeBoolean(source.scan_mail, DEFAULT_SETTINGS.scan_mail),
    scan_drive: normalizeBoolean(source.scan_drive, DEFAULT_SETTINGS.scan_drive),
    scheduler: {
      enabled: normalizeBoolean(schedulerSource.enabled, DEFAULT_SETTINGS.scheduler.enabled),
      interval_hours: normalizeInteger(
        schedulerSource.interval_hours,
        DEFAULT_SETTINGS.scheduler.interval_hours,
      ),
      run_on_startup: normalizeBoolean(
        schedulerSource.run_on_startup,
        DEFAULT_SETTINGS.scheduler.run_on_startup,
      ),
      last_run: normalizeText(schedulerSource.last_run),
      next_run: normalizeText(schedulerSource.next_run),
    },
  };
}

export function normalizePayload(payload) {
  const source = asObject(payload, "Profile payload is not an object.");
  if (source.schema !== PROFILE_SCHEMA) {
    throw new Error(`Unsupported profile schema: ${String(source.schema)}`);
  }

  const accounts = normalizeArray(source.accounts).map(normalizeAccount);
  const rules = normalizeArray(source.rules).map(normalizeRule);

  return {
    schema: PROFILE_SCHEMA,
    app: normalizeText(source.app, "UniversalMailCleaner"),
    exported_at: normalizeText(source.exported_at),
    accounts,
    rules,
    settings: normalizeSettings(source.settings),
  };
}

export function parsePayloadText(text) {
  if (typeof text !== "string" || text.trim() === "") {
    throw new Error("Profile JSON is empty.");
  }
  return normalizePayload(JSON.parse(text));
}

export function summarizeRule(rule) {
  const labels = {
    older_than_days: `Older than ${rule.value} days`,
    sender: `Sender contains ${rule.value}`,
    subject: `Subject contains ${rule.value}`,
    size_mb: `Larger than ${rule.value} MB`,
  };
  return labels[rule.filter_type] || `${rule.filter_type}: ${rule.value}`;
}

export function filterRules(rules, query = "", status = "all") {
  const needle = query.trim().toLowerCase();
  return normalizeArray(rules).filter((rule) => {
    if (status === "active" && !rule.active) {
      return false;
    }
    if (status === "inactive" && rule.active) {
      return false;
    }
    if (!needle) {
      return true;
    }
    const haystack = [
      rule.name,
      rule.target_account,
      rule.filter_type,
      rule.value,
      summarizeRule(rule),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(needle);
  });
}

export function formatScheduler(settings) {
  const scheduler = settings.scheduler;
  if (!scheduler.enabled) {
    return "Disabled";
  }
  const startup = scheduler.run_on_startup ? "startup on" : "startup off";
  return `Every ${scheduler.interval_hours}h, ${startup}`;
}

export function createDemoPayload() {
  return normalizePayload({
    schema: PROFILE_SCHEMA,
    app: "UniversalMailCleaner",
    exported_at: "2026-06-22T01:30:00+02:00",
    accounts: [
      {
        name: "Büro Köln",
        protocol: "IMAP",
        host: "imap.example.de",
        port: 993,
        user: "buero@example.de",
        trash_folder: "Papierkorb",
      },
      {
        name: "Privat Gmail",
        protocol: "Gmail API",
        host: "",
        port: 0,
        user: "maria@example.com",
        trash_folder: "",
      },
    ],
    rules: [
      {
        name: "Newsletter älter als 90 Tage",
        target_account: "Büro Köln",
        filter_type: "older_than_days",
        value: "90",
        active: true,
      },
      {
        name: "Werbung von Reiseportalen",
        target_account: "Privat Gmail",
        filter_type: "sender",
        value: "reisen@example.org",
        active: false,
      },
    ],
    settings: {
      safe_mode: true,
      selected_rule_folders: ["INBOX", "Newsletters"],
      large_item_threshold_mb: 15,
      scan_mail: true,
      scan_drive: false,
      scheduler: {
        enabled: true,
        interval_hours: 24,
        run_on_startup: false,
        last_run: "2026-06-21T22:15:00+02:00",
        next_run: "2026-06-22T22:15:00+02:00",
      },
    },
  });
}
