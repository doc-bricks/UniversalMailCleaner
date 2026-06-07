# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Added
- Source-platform smoke (`tests/source_platform_smoke.py`) for macOS and Linux with
  GitHub Actions CI on ubuntu-latest and macos-latest (PySide6 offscreen, 6 checks)
- Gmail cleanup rules now run against Gmail API accounts in addition to IMAP accounts
- Large-mail scan, delete, and undo now work for Gmail API accounts
- Large-item scan now optionally includes Google Drive files for Gmail API accounts
- Regression tests for Gmail backend routing, Gmail service helpers, and scheduler behavior
- Secrets-free profile export/import for `universalmailcleaner-profile-v1.json`

### Changed
- Large-mail account selection now includes Gmail API accounts
- Folder selection dialog is limited to IMAP accounts because Gmail rules do not use IMAP folders
- IMAP large-mail deletion now respects the original folder of each selected mail
- Gmail OAuth now requests full Drive access and discards cached tokens that only have the old read-only Drive scope
- Google client libraries are now imported lazily so IMAP-only setups still
  start even when the optional Gmail packages are not installed
- README copy, screenshot alt text, app title, and discovery metadata now describe UniversalMailCleaner as a local-first Gmail and IMAP cleanup app
- README and `llms.txt` now include clearer start points and search/disambiguation wording for Gmail cleanup, IMAP mailbox cleanup, large-mail finding, and local-first Windows mail management
- Scan settings, selected IMAP target folders, and scheduler exchange settings now persist in the desktop config and portable profile

### Fixed
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
