# UniversalMailCleaner - Projektanalyse

> Erstellt via ATI #4802 - Standardaufnahmeverfahren

## Uebersicht

| Eigenschaft | Wert |
|-------------|------|
| **Name** | MailCleaner_V8_Universal |
| **Typ** | Desktop GUI Tool (PyQt6) |
| **Hauptdatei** | `mail_imap_cleaner_v1.py` |
| **Sprache** | Python 3 |
| **Status** | Funktionsfaehig / Produktiv |

## Features

1. **Multi-Account IMAP Management**
   - Mehrere E-Mail-Konten verwalten (GMX, Gmail, etc.)
   - IMAP4_SSL Verbindung mit Keyring-Passwortspeicherung
   - Auto-Detect fuer Papierkorb-Ordner

2. **Regelbasiertes Aufraeumen**
   - Filter: Alter (Tage), Absender, Betreff, Groesse (MB)
   - Regeln pro Account oder fuer alle Accounts
   - Einzel- oder Batch-Ausfuehrung

3. **Grosse Mails Scanner**
   - Mails ueber einstellbarem Schwellwert (MB) finden
   - Checkbox-basierte Auswahl zum Loeschen
   - Zeigt Betreff, Groesse, Datum an

4. **Sicherheitsmodus**
   - Safe Mode: Mails werden erst in Papierkorb verschoben
   - Unsafe Mode: Mails werden sofort endgueltig geloescht
   - Toggle in Einstellungen

5. **Dark Theme UI**
   - Dunkles Farbschema fuer die gesamte Anwendung
   - Tab-basiertes Layout (Accounts, Regeln, Grosse Mails, Settings, Log)

## Architektur

```
mail_imap_cleaner_v1.py (Einzeldatei-Architektur)
├── Data Models
│   ├── MailAccount (dataclass)
│   └── CleanRule (dataclass)
├── IMAP Logic
│   └── ImapService (Verbindung, Suche, Papierkorb-Erkennung)
├── Worker (QThread)
│   ├── run_rules() - Regelausfuehrung
│   ├── scan_large() - Grosse Mails finden
│   └── delete_items() - Markierte loeschen
├── GUI Dialogs
│   ├── AccountDialog
│   └── RuleDialog
└── MainWindow
    ├── Tab: Accounts
    ├── Tab: Regeln
    ├── Tab: Grosse Mails
    ├── Tab: Einstellungen
    └── Tab: Log
```

## Dependencies

| Paket | Verwendung | Typ |
|-------|-----------|-----|
| PyQt6 | GUI Framework | Extern (pip) |
| keyring | Sichere Passwortspeicherung | Extern (pip, optional) |
| imaplib | IMAP Protokoll | Stdlib |
| email | E-Mail Parsing | Stdlib |
| json | Konfiguration speichern | Stdlib |
| logging | Log-Ausgaben | Stdlib |
| dataclasses | Datenmodelle | Stdlib |

## Konfiguration

- Konfigurationsdatei: `~/.mail_cleaner/config.json`
- Enthaelt: Accounts, Regeln, Einstellungen (safe_mode)
- Passwoerter via `keyring` (OS-Credential-Store)

## Staerken

- Saubere Trennung von Datenmodellen, IMAP-Logik und GUI
- Thread-basierte Verarbeitung (keine GUI-Blockade)
- Safe-Mode als Default schuetzt vor versehentlichem Datenverlust
- Auto-Detect fuer Provider-spezifische Ordnernamen

## Verbesserungspotenzial

- Einzeldatei-Architektur (607 Zeilen) - koennte modularisiert werden
- Kein requirements.txt vorhanden
- Kontextmenu bei Regeln hat einen Bug (triggered-Signal wird sofort ausgewertet statt verbunden)
- Kein Undo fuer Loeschaktionen
- Nur INBOX wird gescannt, keine weiteren Ordner
