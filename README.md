# UniversalMailCleaner

Desktop-Tool zum regelbasierten Aufräumen von IMAP-Postfächern mit Safe-Mode, Mehrordner-Support und Undo für Papierkorb-Aktionen.
Desktop tool for cleaning IMAP mailboxes with rule-based filters, safe trash mode, multi-folder support, and undo for trash operations.

![UniversalMailCleaner Vorschau](README/screenshots/main.png)

## Überblick

UniversalMailCleaner ist für lokale Mail-Aufräumroutinen gedacht: mehrere Konten verwalten, Regeln definieren, große Mails finden und Löschaktionen standardmäßig sicher über den Papierkorb ausführen.

## Funktionen / Features

- Multi-Account-Management für IMAP-Provider wie GMX, Gmail und Outlook
- Sichere Passwortspeicherung via `keyring` mit Fallback ohne Persistenz
- Regelbasierte Filter für Alter, Absender, Betreff und Größe
- Mehrordner-Support statt reiner INBOX-Verarbeitung
- Safe-Mode per Papierkorb und Unsafe-Mode für endgültiges Löschen
- Undo für Safe-Mode-Löschaktionen
- Scanner für große Mails mit tabellarischer Auswahl
- Konfigurierbares Logging über `UMAIL_CLEANER_LOG_LEVEL`
- Modulare Struktur mit `imap_client.py`, `models.py` und `workers.py`

## Start / Run

### Windows

- `START.bat` ausführen

### Manuell / Manual

```bash
pip install -r requirements.txt
python mail_imap_cleaner_v1.py
```

## Typischer Workflow

1. IMAP-Konto anlegen
2. Papierkorb-Ordner prüfen oder auto-erkennen lassen
3. Regel definieren oder Scanner für große Mails nutzen
4. Zielordner für die Regelausführung auswählen
5. Aktion im Safe-Mode ausführen
6. Falls nötig letzte Löschung rückgängig machen

## Konfiguration

- Lokale Konfigurationsdatei: `%USERPROFILE%\.mail_cleaner\config.json`
- Passwörter werden nicht in der JSON-Datei gespeichert
- Safe-Mode ist standardmäßig aktiv

## Tests

```bash
pytest tests -v
python -m unittest discover tests
```

Aktuell vorhanden:

- Unit-Tests für `ImapService.get_search_criteria()`
- Tests für den modularisierten IMAP-Service

## Sicherheit / Safety

- IMAP läuft über verschlüsselte Verbindungen (`IMAP4_SSL`)
- Safe-Mode verschiebt Mails standardmäßig in den Papierkorb
- Undo steht für Safe-Mode-Aktionen zur Verfügung
- Ohne `keyring` werden Passwörter nur für die aktuelle Session gehalten

## Unterstützte Provider

- GMX (`imap.gmx.net:993`)
- Gmail (`imap.gmail.com:993`) mit App-Passwort
- Outlook (`outlook.office365.com:993`)
- Weitere IMAP4-Provider mit Standard-SSL-Setup

## Lizenz / License

[MIT](LICENSE)

## English

UniversalMailCleaner is a desktop application for cleaning IMAP mailboxes with rule-based filters, large-mail scanning, multi-folder execution, and safe trash-first deletion.

### Highlights

- Multi-account IMAP support
- Folder-aware rule execution
- Safe mode plus undo for trash operations
- Optional OS keyring integration
- Configurable logging

### License

MIT License

## FAQ

### Gmail login fails?

Enable two-factor authentication and create an app password:
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

### Keyring is missing?

Install it via `pip install keyring`.

### Trash folder was not detected?

Set the trash folder manually in the account dialog.
