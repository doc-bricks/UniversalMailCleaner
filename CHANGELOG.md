# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Fixed
- **RFC 3501 IMAP Date Format Locale Isolation (IMAP-003):**
  - Resolved query syntax errors (`BAD Invalid date in SEARCH command`) during `older_than_days` IMAP rule searches on non-English (e.g. German `de_DE`) host locales.
  - Implemented `format_imap_date` in `imap_client.py` using fixed RFC 3501 English month tokens (`Jan`..`Dec`) rather than runtime-locale-dependent `strftime("%d-%b-%Y")` (which produced localized abbreviations like `Mrz`, `Mai`, `Okt`, `Dez`).
  - Added test coverage in `tests/test_imap_service.py` verifying RFC 3501 date-text formatting across all 12 calendar months and explicitly under active German locale.

### Added
- **Pfad B Discoverability, Visual 4-View Architecture, Level 1 SBOM Stand 2026-10-03 & Contract Test Expansion (2026-10-03):**
  - Integrated ASCII Four-View Architectural Topology projection in Section 1 of both `README.md` and `README_de.md` (and byte-identical `README-DE.md`) detailing View 1 (Caller Runtimes, Desktop User Interaction & UI Controls), View 2 (Core Filter & Asynchronous Worker Engine), View 3 (Secure OS Keyring & Protocol Storage Tiers), and View 4 (Air-Gap Defense Perimeter, Zero-Egress & Data Safety Boundaries) with complete invariant mappings (`INV-LOCAL-01` to `INV-SLA-10`).
  - Re-audited Level 1 SBOM in `THIRD_PARTY_LICENSES.md` and plain-text companion `THIRD_PARTY_LICENSES.txt` for Stand 2026-10-03, verifying weak copyleft isolation for PySide6 LGPL-3.0, unprivileged `RunAsInvoker` user mode execution (`INV-USER-02`), and statutory liability limitation under German civil code (§ 521 BGB Gefälligkeitsrecht).
  - Synchronized repository verification badges to `2026-10-03` and updated test pass baseline across English and German documentation.
  - Updated LLM context index (`llms.txt`) with 2026-10-03 currency, Four-View Topology reference, and contract test metrics.
  - Expanded automated contract test suite in `tests/test_metadata.py` with tests for ASCII Four-View Topology parity, 2026-10-03 verification recency, and Level 1 SBOM audit freshness (total 117 passed, 100% green).
- **Pfad A Technical Hygiene, CI Lifecycle Workflows, PEP 621 Standardisation & Contract Test Expansion (2026-10-01):**
  - Provisioned automated PR assignment lifecycle workflow (`.github/workflows/auto-assign.yml`) using `actions/github-script@v7`, 5-minute timeout guardrail, concurrency isolation (`auto-assign-${{ github.ref }}`, `cancel-in-progress: true`), and least-privilege permissions (`issues: write`, `pull-requests: write`).
  - Provisioned label synchronisation workflow (`.github/workflows/label-sync.yml`) using `EndBug/label-sync@v2`, 5-minute timeout guardrail, concurrency isolation (`label-sync-${{ github.ref }}`, `cancel-in-progress: true`), and least-privilege permissions (`issues: write`).
  - Added canonical `.github/labels.yml` definition with 11 standard labels adhering to `GOVERNANCE.md` §4.2.
  - Enhanced `CONTRIBUTING.md` with bilingual contribution instructions, comprehensive mapping of all 10 governance and runtime invariants (`INV-LOCAL-01` to `INV-SLA-10`), unprivileged `RunAsInvoker` user mode execution (`INV-USER-02`), Plan D local development workflow, and version freeze discipline under `T-20260920-167562623`.
  - Re-audited Level 1 SBOM text companion `THIRD_PARTY_LICENSES.txt` (Stand 2026-10-01) with full invariant cross-reference matrix table, § 521 BGB statutory notice, 48h Security Response SLA, and root `NOTICE` cross-reference.
  - Re-audited `THIRD_PARTY_LICENSES.md` for Stand 2026-10-01.
  - Hardened `.gitignore` multi-host and lock defense: added `Desktop.ini`, `*-IDEAPAD-GEI*`, `LOCK.dev.*`, `LOCK.antigravity.*`, `LOCK.bugsearch.*`, and `TASKPLAN_*.md`.
  - Standardized PEP 621 metadata in `pyproject.toml`: registered `Contributing`, `Plain-Text License`, `Third-Party Licenses (Text)`, and `Level 1 SBOM` URLs under `[project.urls]`. Strictly preserved version `1.2.0` under freeze discipline `T-20260920-167562623`.
  - Added 6 new automated contract tests in `tests/test_metadata.py` verifying auto-assign workflow, label-sync workflow, canonical labels, contributing guide invariants, plain-text SBOM companion, extended PEP 621 URLs, and multi-host gitignore guards (total 114 passed, 100% green).
  - Synchronized documentation badges, verification timestamps (2026-10-01), and LLM context index (`llms.txt`).
- **Pfad A Technical Hygiene, CI Lifecycle Hardening, Multi-Host Defense & Contract Test Expansion (2026-09-26):**
  - Added `.github/workflows/welcome.yml` with `actions/first-interaction@v3`, 5-minute timeout guardrail, concurrency isolation (`cancel-in-progress: true`), and least-privilege permissions (`issues: write`, `pull-requests: write`).
  - Hardened `.github/workflows/stale.yml` with concurrency isolation group `stale-${{ github.ref }}` and `cancel-in-progress: true`.
  - Expanded `.gitignore` multi-host conflict defense (`*-ASUS-GEI*`, `*-MacBook*`, `*-IDEAPAD*`, `*_WORKSTATION*`, `*_WORKSTATION-LG*`, `*-WORKSTATION.*`, `*-WORKSTATION-LG.*`), canonical multi-agent lock patterns (`LOCK.user.*`, `LOCK.until.*`, `LOCK.condition.*`, `.automation-lock`), and test cache directories (`.pytest_temp/`, `.pytest_tmp*/`, `.nyc_output/`).
  - Hardened `pyproject.toml` PEP 621 metadata: included `THIRD_PARTY_LICENSES.txt` in `license-files`, specified `minversion = "7.0"`, hardened `addopts = "-ra -v --basetemp=.pytest_temp"`, and added comprehensive `norecursedirs` list; strictly preserved version `1.2.0` under freeze discipline `T-20260920-167562623`.
  - Re-audited `THIRD_PARTY_LICENSES.md` for Stand 2026-09-26 and added `RunAsInvoker` unprivileged user mode execution certification (`INV-USER-02`).
  - Synchronized documentation badges, verification timestamps (2026-09-26), and LLM context index (`llms.txt`).
  - Expanded automated contract test suite in `tests/test_metadata.py` with contract tests for welcome workflow, stale concurrency, gitignore patterns, and PEP 621 pytest configuration.
- **Pfad B Discoverability, Visual Architecture, Level 1 SBOM & Navigation Modernization (2026-09-22):**
  - Standardized documentation quick navigation to the 18-point dual-anchor architecture with reciprocal anchors (`<a id="sec-XX"></a><a id="..."></a>`) across `README.md`, `README_de.md`, and byte-identical `README-DE.md`.
  - Added canonical root `NOTICE` attribution file declaring copyright (c) 2026 Lukas Geiger, doc-bricks, and open-bricks.
  - Added Level 1 SBOM Invariant Cross-Reference Matrix (Section 7) to `THIRD_PARTY_LICENSES.md` auditing `INV-LOCAL-01` through `INV-SLA-10`.
  - Modernized `pyproject.toml` with `license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md"]`, expanded 20 saturated keywords, and added `"Notice"` project URL.
  - Formulated Section 18 Statutory Notice under German § 521 BGB (Gefälligkeitsrecht) and reaffirmed 48h Security Response SLA.
  - Updated `llms.txt` with refreshed audit date (2026-09-22), `NOTICE` reference, Level 1 SBOM, and § 521 BGB disclaimer.
  - Expanded contract testsuite in `tests/test_metadata.py` validating root NOTICE, 20 PEP 621 keywords, 18 navigation sections, and version freeze discipline.
- **Accessibility & UX Navigation Overhaul (2026-09-18):**
  - Implementierte vollständige Barrierefreiheit nach WCAG 2.1 AA / Screenreader-Standards für alle primären Navigations-Tabs (`Hauptbereiche`) inklusive aussagekräftiger Tooltips für sämtliche 8 Reiter.
  - Ergänzte semantische `accessibleName`-, `accessibleDescription`- und Tooltip-Attribute für alle zentralen Aktionsschaltflächen, Tabellen und Einstellungssteuerungen über Konten, Filterregeln, Großmail-Scan, Zeitplaner und Gmail-Labels.
  - Ausstattete Scanergebnis-Zeilen mit kontextbezogenen Checkbox-Tooltips (`Auswählen für Bereinigung: <Betreff> (<Größe> MB)`) und `AccessibleTextRole` für assistive Bildschirmleser.
  - Ergänzte intuitive Desktop-Tastenkürzel für Kernaktionen: `F5` zum Starten des Großmail-Scans und `Del` / `Entf` zum Bereinigen ausgewählter Elemente.
  - Erweiterte automatisierte Barrierefreiheits-Vertragstests in `tests/test_main_window.py` und `tests/test_scheduler_widget.py`.
- **App-Icon-Generator & Multi-Variant-Asset-System (2026-09-14):**
  - Aufbereitung und Hochskalierung des Original-App-Icons auf ein verlustfreies 1024x1024 Master-Icon (`UniversalMailCleaner_icon.png`, `icon.png`, `DesktopIcon.png`).
  - Generierung vollständiger 7-Layer Multi-Resolution Windows ICO-Dateien (`UniversalMailCleaner_icon.ico`, `icon.ico`, `DesktopIcon.ico`) mit den standardisierten Dimensionen 16x16, 24x24, 32x32, 48x48, 64x64, 128x128 und 256x256 Pixeln.
  - Bereitstellung von 4-Layer Favicons (`favicon.ico`: 16x16, 24x24, 32x32, 48x48) im Root-, `assets/`- und `mobile_icons/`-Verzeichnis sowie `favicon.png` (32x32) und Apple Touch Icons (`apple-touch-icon.png`, `apple-touch-icon-180.png`: 180x180).
  - PWA- und Mobile-Icon-Paket (`mobile_icons/`): Standard- und Maskable-Icons (`icon-192.png`, `icon-512.png`, `icon-maskable-192.png`, `icon-maskable-512.png`) inklusive validem Web-App-Manifest (`manifest.json`) mit Safespace-Pufferung.
  - Microsoft Store Asset-Paket (`store_assets/`): Standardisierte Windows-Store- und WinGet-Kachelgrößen (`icon_44x44.png`, `Square44x44Logo.png`, `icon_50x50.png`, `StoreLogo.png`, `icon_150x150.png`, `Square150x150Logo.png`, `icon_310x310.png`, `Square310x310Logo.png`, `icon_310x150.png`, `Wide310x150Logo.png`) nebst Dokumentation `store_assets/README.md`.
  - Laufzeit-Einbindung des Anwendungs-Icons (`get_app_icon()` in `mail_imap_cleaner_v1.py`) für Hauptfenster (`MainWindow.setWindowIcon`) und Prozessinstanz (`QApplication.setWindowIcon`) mit robuster Pfadauflösung (PyInstaller-Bundle `sys._MEIPASS`, Anwendungsroot, Assets-Ordner).
  - PyInstaller-Spec-Update (`UniversalMailCleaner.spec`) zur Bündelung des `assets/`-Verzeichnisses in Release-Builds.
  - Automatisierte Vertragstest-Suite in `tests/test_assets_and_icons.py` (5 Vertragstests zur Validierung von Root-Icons, 7 ICO-Layern, PNG-Dimensionen, PWA-Manifest, Store-Kacheln und Laufzeit-Icon-Auflösung).
- **Pfad A Technical Hygiene, CI/CD Hardening, Multi-Host Defense & Security Policy (2026-09-14):**
  - Configured multi-OS CI/CD workflow (`.github/workflows/ci.yml`) spanning Windows, Ubuntu, and macOS with Python 3.10-3.12 matrix, pip caching, bytecode compilation verification (`compileall`), Ruff linting, and automated Pytest test suite with 15-minute runaway timeout guardrail and concurrency isolation (`cancel-in-progress: true`).
  - Hardened source-platform smoke workflow (`.github/workflows/source-platform-smoke.yml`) with job-level `timeout-minutes: 15` and concurrency group.
  - Added automated Stale Issues & PRs lifecycle workflow (`.github/workflows/stale.yml`) with `actions/stale@v9`, daily 01:30 UTC schedule, 30-day stale / 7-day close thresholds, and `timeout-minutes: 10`.
  - Hardened `.gitignore` against multi-host cloud-sync conflicts (`* (kopie)*`, `* (copy)*`, `*conflicted copy*`, `*-ASUS*`, `*-WORKSTATION*`, `*-LAPTOP*`, `*.sync-conflict-*`), multi-agent lock systems (`LOCK`, `LOCK.*`, `LOCK.permissions.json`, `uv.lock`), and coverage/build artifacts.
  - Standardized PEP 621 project URLs in `pyproject.toml` with `Bug Tracker`, `Parent Organization`, and `Umbrella Ecosystem` pointers; configured `[tool.pytest.ini_options]` with `addopts = "-ra -v"`; expanded Ruff linter rulesets with `C4` (flake8-comprehensions).
  - Authored comprehensive bilingual Security Policy (`SECURITY.md`) establishing 48-hour response SLA and 5-day triage (`INV-SLA-10`), supported versions lifecycle (1.2.x), direct security coordinator contacts, private vulnerability advisory paths, and architectural local-first / zero-egress / non-elevated user-mode guarantees.
  - Added 6 automated metadata contract tests in `tests/test_metadata.py` validating CI timeouts and concurrency, stale lifecycle automation, gitignore multi-host and lock defense, PEP 621 URL definitions and pytest options, bilingual security policy invariants, and changelog/marketing log recency.

## [1.2.0] - 2026-09-12

### Added
- **Pfad B Discoverability, Visual Architecture & Governance Parity (2026-09-12):**
  - Upgraded documentation with 15-point quick navigation across `README.md`, `README_de.md`, and `README-DE.md` with 100% reciprocal anchor parity.
  - Implemented Dual-Mermaid diagrams: 4-layer system architecture (`flowchart TD`) and transactional email cleanup & safe-trash lifecycle (`sequenceDiagram`), fully validated via `lint_mermaid.py`.
  - Audited and documented 10 Governance- and Runtime-Invariants (`INV-LOCAL-01` through `INV-SLA-10`).
  - Cataloged 4 Target Personas (Privacy-Conscious Professionals & GDPR Officers, Storage-Constrained Account Holders, Power Users, and Solo Developers).
  - Designed 5-way comparative matrix across 10 architectural and operational dimensions.
  - Generated comprehensive third-party license inventory `THIRD_PARTY_LICENSES.md` auditing runtime dependencies (PySide6, keyring, google packages), transitive libraries, and unbundled OS services.
  - Published dedicated repository marketing log `MARKETING-LOG.txt`.
  - Added PEP 621 extended project URLs (`Third-Party Licenses`, `Marketing Log`, `LLM Ready`, `Security Policy`, `Issues`) in `pyproject.toml`.
  - Expanded contract testsuite in `tests/test_metadata.py` covering navigation anchors, 10 invariants, personas, comparative matrix, license audit, and German README parity.
  - Updated `llms.txt` with current 2026-09-12 timestamp, invariants, personas, and ecosystem pointers.
- Discoverability, README-Design, Badges & Metadata Parity Check (2026-08-16):
  - Synchronized badges across `README.md`, `README-DE.md`, and `README_de.md` (81 Tests Passed, Version 1.2.0, `doc-bricks` organization, `open-bricks` ecosystem umbrella, `llms.txt` discovery).
  - Integrated interactive bilingual Mermaid system architecture diagrams in documentation.
  - Linked sibling tools matrix across `doc-bricks`, `file-bricks`, and `open-bricks` suites (`MailProcessor`, `UniversalDocsGrabber`, `UniversalInvoiceMail`, `DokuZen`, `PDFtoPDFocr`, `MediaBrain`, `ProFiler`).
  - Added automated metadata, manifest, and discoverability test suite in `tests/test_metadata.py` (5/5 checks passed, total 81 passed).
  - Configured `[tool.ruff]` and `[tool.ruff.lint]` in `pyproject.toml` (100% clean check).
  - Updated `llms.txt` with ecosystem pointers and verified last-checked timestamp `2026-08-16`.
- Discoverability, README-Design & SEO Check (2026-07-30): Added `organization: doc-bricks` & Python version shields to `README.md` and `README-DE.md`, updated `pyproject.toml` keywords (`gmail`, `imap`, `mailbox-cleaner`, `pyside6`, `windows`) & URLs (`Documentation`, `Changelog`), verified 65 Pytest unit tests.
- open-bricks ecosystem badges and `llms.txt` callout notes added to `README.md` and `README-DE.md` for enhanced Discoverability and machine-readable indexing
- Source-platform smoke (`tests/source_platform_smoke.py`) for macOS and Linux with
  GitHub Actions CI on ubuntu-latest and macos-latest (PySide6 offscreen, 6 checks)
- Gmail cleanup rules now run against Gmail API accounts in addition to IMAP accounts
- Large-mail scan, delete, and undo now work for Gmail API accounts
- Large-item scan now optionally includes Google Drive files for Gmail API accounts
- Regression tests for Gmail backend routing, Gmail service helpers, and scheduler behavior
- Secrets-free profile export/import for `universalmailcleaner-profile-v1.json`
- `pyproject.toml` with setuptools metadata, GUI entry point, and shared pytest/Ruff configuration

### Changed
- German community and contribution documentation now consistently uses UTF-8 umlauts; `llms.txt` records the current repository-hygiene review date.
- Large-mail account selection now includes Gmail API accounts
- Folder selection dialog is limited to IMAP accounts because Gmail rules do not use IMAP folders
- IMAP large-mail deletion now respects the original folder of each selected mail
- Gmail OAuth now requests full Drive access and discards cached tokens that only have the old read-only Drive scope
- Google client libraries are now imported lazily so IMAP-only setups still
  start even when the optional Gmail packages are not installed
- README copy, screenshot alt text, app title, and discovery metadata now describe UniversalMailCleaner as a local-first Gmail and IMAP cleanup app
- README and `llms.txt` now include clearer start points and search/disambiguation wording for Gmail cleanup, IMAP mailbox cleanup, large-mail finding, and local-first Windows mail management
- README, README-DE, and `llms.txt` now include exact `doc-bricks/UniversalMailCleaner` search anchors and clearer disambiguation from anti-spam gateways, mailing-list cleaners, unsubscribe services, and browser-only Gmail extensions
- Scan settings, selected IMAP target folders, and scheduler exchange settings now persist in the desktop config and portable profile
- CI: source-platform smoke workflow `paths:` filter removed so the smoke now triggers on changes to any module (`imap_client`, `models`, `gmail_service`, `profile_exchange`), not just the main file
- `mail_imap_cleaner_v1.py` exposes `main()` so editable installs and GUI entry points can launch the existing desktop app without wrapper scripts

### Fixed
- `workers.py`: IMAP large-mail scan, deletion, and undo now use UIDs with `UIDVALIDITY` epochs. Safe-mode deletion requires UIDPLUS before copying, verifies the complete `COPYUID` mapping, and every deletion uses UID-specific `EXPUNGE`, preventing unsafe references, orphaned copies, and unrelated expunges.
- `imap_client.py` / `get_search_criteria`: Guard against wildcard matches from empty or whitespace filter values (`sender`, `subject`), non-positive days (`older_than_days <= 0`), and non-positive sizes (`size_mb <= 0`), returning `None` instead of generating queries that match all emails.
- `workers.py` / `run_rules` & `scan_large`: Safely handle `[None]` data payloads from `search()` without raising `AttributeError`.
- `mail_imap_cleaner_v1.py`: Die Einstellungen sind in der Hauptnavigation nicht mehr nur über ein einzelnes Zahnrad erreichbar; der Tab zeigt jetzt `⚙ Einstellungen` und erklärt den Bereich zusätzlich per Tooltip.
- `mail_imap_cleaner_v1.py` / `closeEvent`: Worker is now stopped before `save_config` to avoid a race condition on window close.
- `mail_imap_cleaner_v1.py` / `save_config`: `OSError` is now caught so a failed config write doesn't crash the app.
- `mail_imap_cleaner_v1.py` / `add_acc`: `keyring.set_password` is now wrapped in try/except to handle missing or locked keyring backends gracefully.
- `workers.py` / `Worker.__init__`: Account list is now snapshotted as a copy, preventing cross-thread mutation with the GUI account list.
- `mail_imap_cleaner_v1.py` / `run_worker`: Stale `data_ready` signal is disconnected before the worker is replaced, avoiding the Qt signal-to-deleted-object crash.
- `mail_imap_cleaner_v1.py` / `_run_label_service_task`: `LabelActionWorker` is now stored in an instance list to prevent it from being garbage-collected while running.
- `imap_client.py` / `run_rules`: `imaplib.IMAP4.error` and `data is None` guard added around `search()` to handle unexpected server responses.
- `imap_client.py` / `scan_large`: Same `imaplib.IMAP4.error` and `data is None` guard added around `search()`.
- `workers.py` / `delete_items`: Added interruption check and per-folder `try/except` for both IMAP and generic errors to avoid silent drop of remaining folders on partial failure.
- `imap_client.py` / `list_folders`: IMAP `LIST` response parser now handles both quoted and unquoted folder names (fixes folders containing spaces, e.g. Exchange `Deleted Items`).
- `imap_client.py` / `find_trash_folder`: Same quoted/unquoted `LIST` parser applied so trash detection works on Exchange and non-standard IMAP servers.
- `workers.py`: guard against missing `Date` header in `scan_large` (`None` slice raised `TypeError`)
- `profile_exchange.py`: guard against `null` settings in `load_profile_payload` (`None or {}` pattern)
- `imap_client.py`: escape backslashes in IMAP quoted strings per RFC 3501 to prevent broken search queries
- `gmail_service.py`: persist refreshed OAuth token to disk so subsequent startups skip re-authentication

## [1.2.0] - 2026-05-02

### Added
- Gmail API Backend als zweiter Account-Typ (google-auth-oauthlib)
- Scheduler-Tab für automatische periodische Bereinigung (QTimer)
- Statistiken-Tab: Gmail-Speicherverbrauch und Drive-Quota
- Labels-Tab: Gmail-Labels anzeigen, Mails nach Label löschen

## [1.1.0] - 2026-04-29

### Hinzugefügt / Added
- Multiple-Folder-Support für Regelausführung und Large-Mail-Scan
- Undo für Safe-Mode-Löschaktionen
- Folder-Auswahldialog im Regeln-Tab

### Geändert / Changed
- Modularisierung in `imap_client.py`, `models.py` und `workers.py`
- Logging-Level jetzt über `UMAIL_CLEANER_LOG_LEVEL` steuerbar
- README an aktuellen Funktionsstand angepasst

### Behoben / Fixed
- IMAP-Injection-Schutz für FROM- und SUBJECT-Filter
- Mehrere generische `except`-Stellen durch Logging und gezielteres Verhalten ersetzt

## [1.0.0] - 2026-02-21

### Hinzugefügt / Added
- Erstveröffentlichung / Initial release
- IMAP4_SSL Multi-Account-Management mit Keyring-Integration
- Regelbasiertes Aufräumsystem (Alter, Absender, Betreff, Größe)
- Safe-Mode (Papierkorb) und Unsafe-Mode (endgültig löschen)
- Großer-Mails-Scanner mit Sortierung
- Dark Theme (Qt-Stylesheet)
- Logging-Level konfigurierbar via UMAIL_CLEANER_LOG_LEVEL
- Unit-Tests für ImapService.get_search_criteria() (9 Tests)
- Docstrings und Type Hints für ImapService und Worker
