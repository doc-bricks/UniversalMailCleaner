# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Added
- Windows Store readiness preflight (`scripts/check_store_readiness.py`),
  `store_package.json`, and `docs/WINDOWS_STORE_READINESS.md` for the
  Partner Center / MSIX / WACK gate.
- Source-platform smoke (`tests/source_platform_smoke.py`) for macOS and Linux with
  GitHub Actions CI on ubuntu-latest and macos-latest (PySide6 offscreen, 6 checks)
- Gmail cleanup rules now run against Gmail API accounts in addition to IMAP accounts
- Large-mail scan, delete, and undo now work for Gmail API accounts
- Large-item scan now optionally includes Google Drive files for Gmail API accounts
- Regression tests for Gmail backend routing, Gmail service helpers, and scheduler behavior
- Secrets-free profile export/import for `universalmailcleaner-profile-v1.json`
- `pyproject.toml` with setuptools metadata, GUI entry point, and shared pytest/Ruff configuration

### Changed
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
- Desktop config writes now use `%LOCALAPPDATA%\UniversalMailCleaner\config.json`
  while still reading legacy `%USERPROFILE%\.mail_cleaner\config.json` installs
  when no new config exists.

### Fixed
- `workers.py`: `finished = Signal(str)` überschattete das parameterlose `QThread.finished`-Lifecycle-Signal.
  Das Custom-Signal heißt jetzt `task_done = Signal(str)`; `mail_imap_cleaner_v1.py` verbindet entsprechend
  `task_done`. Damit reagiert Qt's C++-seitiger Lifecycle-Mechanismus wieder korrekt, wenn der Thread
  unerwartet endet. Regressionstest in `tests/test_bug_regressions_20260623.py` ergänzt.
- `workers.py` / `imap_client.py`: Kritischer Datensicherheits-Bug — alle IMAP-Operationen
  (SEARCH, FETCH, COPY, STORE, EXPUNGE) nutzen jetzt durchgängig UIDs statt
  verbindungslokal gültiger Sequenznummern (MSN). Damit können keine falschen Mails mehr
  gelöscht werden, wenn sich die Mailbox zwischen Scan und Löschen geändert hat.
  `ImapService` erhält `supports_uidplus()` und `uid_expunge()` (RFC 4315 UIDPLUS, mit
  Fallback auf reguläres EXPUNGE). Neue Regressionstests verifizieren, dass MSN-Pfade
  nicht mehr erreichbar sind. IMAP-Undo bleibt sicherheitshalber blockiert bis
  COPYUID-basiertes Trash-Mapping implementiert ist (Teilproblem b).
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
# Changelog

## 2026-06-26
- Sicherheitsfix fuer IMAP-Large-Delete: Scan-Ergebnisse tragen jetzt einen Mailbox-Snapshot
  (UIDVALIDITY/UIDNEXT/EXISTS) pro Ordner, und der Delete-Worker bricht hart ab, wenn sich der
  Ordner seit dem Scan geaendert hat.
- IMAP-Undo wird fuer diese sichere Delete-Historie explizit blockiert, bis eine vollstaendige
  UID/COPYUID-basierte Zuordnung implementiert ist; dadurch werden keine falschen Trash-Mails
  restauriert oder expunged.
