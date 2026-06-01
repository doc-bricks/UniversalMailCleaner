# UniversalMailCleaner Austauschformat

Stand: 2026-06-01
Schema: `universalmailcleaner-profile-v1.json`

## Zweck

Das Format dient als secrets-freier Austausch für UniversalMailCleaner-Profile. Es soll Regeln, Kontometadaten, Safe-Mode- und Scheduler-Vorgaben zwischen Desktop-Installationen übertragen oder einem späteren Web/PWA-Companion lesbar machen.

Es ist kein Backup der Mailbox und kein Synchronisationsprotokoll. Löschhistorien, OAuth-Tokens, Passwörter und konkrete Mail- oder Drive-IDs gehören nicht in dieses Format.

## Beispiel

```json
{
  "schema": "universalmailcleaner-profile-v1",
  "app": "UniversalMailCleaner",
  "exported_at": "2026-06-01T10:00:00+02:00",
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
      "account": "GMX",
      "type": "sender",
      "value": "newsletter@example.org",
      "older_than_days": 90,
      "size_mb": 0,
      "active": true,
      "folders": ["INBOX"]
    }
  ],
  "settings": {
    "safe_mode": true,
    "large_item_threshold_mb": 10,
    "scan_mail": true,
    "scan_drive": false,
    "scheduler": {
      "enabled": false,
      "interval_minutes": 60,
      "run_on_startup": false
    }
  }
}
```

## Exportregeln

- Konten dürfen nur Metadaten enthalten: Name, Protokoll, Host, Port, Nutzerkennung und Papierkorb-Ordner.
- Regeln dürfen nur fachliche Filter enthalten: Name, Account-Bezug, Typ, Wert, Alter, Größe, Aktivstatus und Zielordner.
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

Der spätere Import soll defensiv sein:

- Unbekannte Schema-Versionen ablehnen.
- Fehlende optionale Felder mit sicheren Defaults füllen.
- Passwörter und OAuth-Zugänge nach dem Import neu abfragen.
- Nie automatisch Löschaktionen auslösen.
- Konflikte bei bestehenden Konten oder Regeln sichtbar machen statt still zu überschreiben.
