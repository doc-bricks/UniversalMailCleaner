# Changelog / Aenderungsprotokoll

Alle wesentlichen Aenderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [1.2.0] - 2026-05-02
### Added
- Gmail API Backend als zweiter Account-Typ (google-auth-oauthlib)
- Scheduler-Tab für automatische periodische Bereinigung (QTimer)
- Statistiken-Tab: Gmail-Speicherverbrauch und Drive-Quota
- Labels-Tab: Gmail-Labels anzeigen, Mails nach Label löschen

## [1.1.0] - 2026-04-29

### Hinzugefuegt / Added
- Multiple-Folder-Support fuer Regelausfuehrung und Large-Mail-Scan
- Undo fuer Safe-Mode-Loeschaktionen
- Folder-Auswahldialog im Regeln-Tab

### Geaendert / Changed
- Modularisierung in `imap_client.py`, `models.py` und `workers.py`
- Logging-Level jetzt ueber `UMAIL_CLEANER_LOG_LEVEL` steuerbar
- README an aktuellen Funktionsstand angepasst

### Behoben / Fixed
- IMAP-Injection-Schutz fuer FROM- und SUBJECT-Filter
- Mehrere generische `except`-Stellen durch Logging und gezielteres Verhalten ersetzt

## [1.0.0] - 2026-02-21

### Hinzugefuegt / Added
- Erstveroeffentlichung / Initial release
- IMAP4_SSL Multi-Account-Management mit Keyring-Integration
- Regelbasiertes Aufraeumsystem (Alter, Absender, Betreff, Groesse)
- Safe-Mode (Papierkorb) und Unsafe-Mode (endgueltig loeschen)
- Grosser-Mails-Scanner mit Sortierung
- Dark Theme (Qt-Stylesheet)
- Logging-Level konfigurierbar via UMAIL_CLEANER_LOG_LEVEL
- Unit-Tests fuer ImapService.get_search_criteria() (9 Tests)
- Docstrings und Type Hints fuer ImapService und Worker
