import {
  STORAGE_KEY,
  createDemoPayload,
  filterRules,
  formatScheduler,
  parsePayloadText,
  summarizeRule,
} from "./library.mjs";

const state = {
  payload: null,
};

const elements = {
  fileInput: document.querySelector("#file-input"),
  pickFile: document.querySelector("#pick-file"),
  togglePaste: document.querySelector("#toggle-paste"),
  loadPaste: document.querySelector("#load-paste"),
  loadDemo: document.querySelector("#load-demo"),
  clearData: document.querySelector("#clear-data"),
  pastePanel: document.querySelector("#paste-panel"),
  pasteJson: document.querySelector("#paste-json"),
  statusBanner: document.querySelector("#status-banner"),
  statAccounts: document.querySelector("#stat-accounts"),
  statRules: document.querySelector("#stat-rules"),
  statSafeMode: document.querySelector("#stat-safe-mode"),
  statScheduler: document.querySelector("#stat-scheduler"),
  accountsList: document.querySelector("#accounts-list"),
  rulesList: document.querySelector("#rules-list"),
  settingsList: document.querySelector("#settings-list"),
  ruleSearch: document.querySelector("#rule-search"),
  ruleStatus: document.querySelector("#rule-status"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setStatus(message, tone = "info") {
  elements.statusBanner.textContent = message;
  elements.statusBanner.dataset.tone = tone;
}

function formatDate(value) {
  if (!value) {
    return "Not available";
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function persistPayload(payload) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function clearPayload() {
  state.payload = null;
  localStorage.removeItem(STORAGE_KEY);
  render();
  setStatus("Offline cache cleared. Load a new secrets-free profile export.", "info");
}

function renderStats() {
  const payload = state.payload;
  if (!payload) {
    elements.statAccounts.textContent = "0";
    elements.statRules.textContent = "0";
    elements.statSafeMode.textContent = "Unknown";
    elements.statScheduler.textContent = "Unknown";
    return;
  }

  elements.statAccounts.textContent = String(payload.accounts.length);
  elements.statRules.textContent = String(payload.rules.length);
  elements.statSafeMode.textContent = payload.settings.safe_mode ? "Enabled" : "Disabled";
  elements.statScheduler.textContent = formatScheduler(payload.settings);
}

function renderAccounts() {
  const payload = state.payload;
  if (!payload) {
    elements.accountsList.classList.add("empty-state");
    elements.accountsList.textContent = "No profile loaded yet.";
    return;
  }

  elements.accountsList.classList.remove("empty-state");
  elements.accountsList.innerHTML = payload.accounts
    .map((account) => {
      const serverLabel =
        account.protocol === "Gmail API"
          ? "OAuth desktop account"
          : `${escapeHtml(account.host)}:${escapeHtml(account.port)}`;
      const trashLabel = account.trash_folder || "Auto-detect / desktop-specific";

      return `
        <article class="card">
          <div class="card-topline">
            <h3>${escapeHtml(account.name)}</h3>
            <span class="chip">${escapeHtml(account.protocol)}</span>
          </div>
          <div class="meta-list">
            <div class="meta-row"><span>User</span><strong>${escapeHtml(account.user || "Not set")}</strong></div>
            <div class="meta-row"><span>Server</span><strong>${serverLabel}</strong></div>
            <div class="meta-row"><span>Trash folder</span><strong>${escapeHtml(trashLabel)}</strong></div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderRules() {
  const payload = state.payload;
  if (!payload) {
    elements.rulesList.classList.add("empty-state");
    elements.rulesList.textContent = "No profile loaded yet.";
    return;
  }

  const rules = filterRules(
    payload.rules,
    elements.ruleSearch.value,
    elements.ruleStatus.value,
  );

  if (rules.length === 0) {
    elements.rulesList.classList.add("empty-state");
    elements.rulesList.textContent = "No rules match the current filter.";
    return;
  }

  elements.rulesList.classList.remove("empty-state");
  elements.rulesList.innerHTML = rules
    .map((rule) => {
      const chipClass = rule.active ? "chip chip-active" : "chip chip-inactive";
      const chipLabel = rule.active ? "Active" : "Inactive";

      return `
        <article class="card">
          <div class="card-topline">
            <h3>${escapeHtml(rule.name)}</h3>
            <span class="${chipClass}">${chipLabel}</span>
          </div>
          <div class="meta-list">
            <div class="meta-row"><span>Account</span><strong>${escapeHtml(rule.target_account)}</strong></div>
            <div class="meta-row"><span>Filter</span><strong>${escapeHtml(rule.filter_type)}</strong></div>
            <div class="meta-row"><span>Value</span><strong>${escapeHtml(rule.value)}</strong></div>
            <div class="meta-row"><span>Summary</span><strong>${escapeHtml(summarizeRule(rule))}</strong></div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderSettings() {
  const payload = state.payload;
  if (!payload) {
    elements.settingsList.classList.add("empty-state");
    elements.settingsList.innerHTML = `
      <div>
        <dt>Status</dt>
        <dd>Load a profile export first.</dd>
      </div>
    `;
    return;
  }

  const scheduler = payload.settings.scheduler;
  elements.settingsList.classList.remove("empty-state");
  elements.settingsList.innerHTML = `
    <div>
      <dt>Exported at</dt>
      <dd>${escapeHtml(formatDate(payload.exported_at))}</dd>
    </div>
    <div>
      <dt>Selected folders</dt>
      <dd>${escapeHtml(payload.settings.selected_rule_folders.join(", "))}</dd>
    </div>
    <div>
      <dt>Large-item threshold</dt>
      <dd>${escapeHtml(payload.settings.large_item_threshold_mb)} MB</dd>
    </div>
    <div>
      <dt>Mail scan</dt>
      <dd>${payload.settings.scan_mail ? "Enabled" : "Disabled"}</dd>
    </div>
    <div>
      <dt>Drive scan</dt>
      <dd>${payload.settings.scan_drive ? "Enabled" : "Disabled"}</dd>
    </div>
    <div>
      <dt>Scheduler</dt>
      <dd>${escapeHtml(formatScheduler(payload.settings))}</dd>
    </div>
    <div>
      <dt>Last run</dt>
      <dd>${escapeHtml(formatDate(scheduler.last_run))}</dd>
    </div>
    <div>
      <dt>Next run</dt>
      <dd>${escapeHtml(formatDate(scheduler.next_run))}</dd>
    </div>
  `;
}

function render() {
  renderStats();
  renderAccounts();
  renderRules();
  renderSettings();
}

function loadPayload(payload, message, tone = "success") {
  state.payload = payload;
  persistPayload(payload);
  render();
  setStatus(message, tone);
}

async function handleFileImport(file) {
  const text = await file.text();
  const payload = parsePayloadText(text);
  loadPayload(payload, `Loaded ${file.name} for offline read-only review.`);
}

function restoreCachedPayload() {
  const cached = localStorage.getItem(STORAGE_KEY);
  if (!cached) {
    render();
    return;
  }
  try {
    state.payload = parsePayloadText(cached);
    render();
    setStatus("Restored the last cached profile export for offline review.", "success");
  } catch (error) {
    localStorage.removeItem(STORAGE_KEY);
    render();
    setStatus(`Stored profile cache was invalid and has been cleared: ${error.message}`, "warning");
  }
}

function setupEvents() {
  elements.pickFile.addEventListener("click", () => elements.fileInput.click());

  elements.fileInput.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    try {
      await handleFileImport(file);
    } catch (error) {
      setStatus(`Import failed: ${error.message}`, "error");
    } finally {
      elements.fileInput.value = "";
    }
  });

  elements.togglePaste.addEventListener("click", () => {
    elements.pastePanel.classList.toggle("hidden");
    if (!elements.pastePanel.classList.contains("hidden")) {
      elements.pasteJson.focus();
    }
  });

  elements.loadPaste.addEventListener("click", () => {
    try {
      const payload = parsePayloadText(elements.pasteJson.value);
      loadPayload(payload, "Pasted JSON imported for offline review.");
    } catch (error) {
      setStatus(`Pasted JSON is invalid: ${error.message}`, "error");
    }
  });

  elements.loadDemo.addEventListener("click", () => {
    loadPayload(createDemoPayload(), "Demo profile loaded. No live mailbox data included.");
  });

  elements.clearData.addEventListener("click", clearPayload);
  elements.ruleSearch.addEventListener("input", renderRules);
  elements.ruleStatus.addEventListener("change", renderRules);
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    return;
  }
  if (window.location.protocol === "file:") {
    setStatus("Running from file:// disables service-worker offline caching. Serve the folder over HTTP for full PWA behavior.", "warning");
    return;
  }
  navigator.serviceWorker.register("./sw.js").catch((error) => {
    setStatus(`Service worker registration failed: ${error.message}`, "warning");
  });
}

setupEvents();
restoreCachedPayload();
registerServiceWorker();
