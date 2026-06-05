# UniversalMailCleaner Austauschformat

Stand: 2026-06-03
Schema: `universalmailcleaner-profile-v1.json`

## Zweck

Das Format dient als secrets-freier Austausch für UniversalMailCleaner-Profile. Es soll Regeln, Kontometadaten, Safe-Mode- und Scheduler-Vorgaben zwischen Desktop-Installationen übertragen oder einem späteren Web/PWA-Companion lesbar machen.

Es ist kein Backup der Mailbox und kein Synchronisationsprotokoll. Löschhistorien, OAuth-Tokens, Passwörter und konkrete Mail- oder Drive-IDs gehören nicht in dieses Format.

## Beispiel

```json
{
  "schema": "universalmailcleaner-profile-v1",
  "app": "UniversalMailCleaner",
  "exported_at": "2026-06-03T16:00:00+02:00",
  "accounts": [
    {
      "name": "Privat Gmail",
      "protocol": "Gmail API",
      "host": "",
      "port": 0,
      "user": "user@example.com",
      "trash_folder": ""
    },
    {
      "name": "GMX",
      "protocol": "IMAP",
      "host": "imap.gmx.net",
      "port": 993,
      "user": "user@gmx.de",
      "trash_folder": "Trash"
    }
  ],
  "rules": [
    {
      "name": "Newsletter älter als 90 Tage",
      "target_account": "GMX",
      "filter_type": "sender",
      "value": "newsletter@example.org",
      "active": true
    }
  ],
  "settings": {
    "safe_mode": true,
    "selected_rule_folders": ["INBOX"],
    "large_item_threshold_mb": 10,
    "scan_mail": true,
    "scan_drive": false,
    "scheduler": {
      "enabled": false,
      "interval_hours": 24,
      "run_on_startup": false
    }
  }
}
```

## Exportregeln

- Konten dürfen nur Metadaten enthalten: Name, Protokoll, Host, Port, Nutzerkennung und Papierkorb-Ordner.
- Regeln dürfen nur fachliche Filter enthalten: Name, Account-Bezug, Filtertyp, Wert und Aktivstatus.
- Die aktuell gewählten IMAP-Zielordner für Regelläufe werden als `selected_rule_folders` in den `settings` gehalten.
- Scheduler-Einstellungen dürfen exportiert werden, solange sie keine lokalen Pfade oder Tokens enthalten.
- Der Export muss UTF-8 schreiben und deutsche Umlaute unverändert erhalten.

## Ausschlüsse

Diese Daten dürfen nicht exportiert werden:

- Passwörter, App-Passwörter, OAuth-Access-Tokens, OAuth-Refresh-Tokens oder `credentials.json`.
- Lokale Keyring-Daten.
- Mail-IDs, Thread-IDs, Drive-Datei-IDs oder Undo-Payloads.
- Löschhistorie, Logdateien oder konkrete Trefferlisten aus Scans.
- Absolute lokale Pfade, sofern sie nicht ausdrücklich als nutzergewählte Import-/Exportziele markiert sind.

## Importverhalten

Der Import soll defensiv sein:

- Unbekannte Schema-Versionen ablehnen.
- Fehlende optionale Felder mit sicheren Defaults füllen.
- Passwörter und OAuth-Zugänge nach dem Import neu abfragen.
- Nie automatisch Löschaktionen auslösen.
- Konflikte bei bestehenden Konten oder Regeln sichtbar machen statt still zu überschreiben.
- Ältere Alias-Felder wie `account` oder `type` dürfen tolerant gelesen werden, wenn sie eindeutig auf die aktuelle Struktur abbildbar sind.
