<img src="assets/banner.svg" width="100%" alt="UniversalMailCleaner Banner">

# UniversalMailCleaner

**[🇬🇧 English documentation](README.md)** · **🇩🇪 Deutsch**

> Lokale Windows-Desktop-App zum Aufräumen von IMAP- und Gmail-Postfächern — regelbasierte Bereinigung, Große-Mail-Scans, Scheduler, Safe-Mode.

[![Lizenz: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v1.2.0-blue)](CHANGELOG.md)
[![Plattform: Windows](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)](#überblick)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41cd52)](https://pypi.org/project/PySide6/)

UniversalMailCleaner bündelt regelbasierte Mail-Bereinigung, große-Mail- und Drive-Scans, geplante Läufe, Safe-Mode und rückgängig machbare Löschaktionen in einer PySide6-Oberfläche.

![UniversalMailCleaner Desktop-Oberfläche für Mailbox-Bereinigung mit Konten, Regeln, großen Elementen, Gmail-Labels, Scheduler und Safe-Mode](README/screenshots/main.png)

## Überblick

UniversalMailCleaner ist für lokale Mail-Aufräumroutinen gedacht: mehrere Konten verwalten, Regeln definieren, große Mails finden und Löschaktionen standardmäßig sicher über den Papierkorb ausführen.

## Warum UniversalMailCleaner

Das Tool richtet sich an Nutzerinnen und Nutzer, die Postfachspeicher und Newsletter-Ballast reduzieren möchten, ohne die eigene Mailbox an einen zusätzlichen Cloud-Dienst zu übergeben. Die App läuft lokal, speichert Passwörter nicht in der Projektkonfiguration, unterstützt normale IMAP-Provider und nutzt die Gmail API nur dort, wo OAuth2-Funktionen gebraucht werden.

## Einstieg

| Wenn du ... | Starte hier |
|---|---|
| ein Gmail-Postfach ohne gehosteten Cleanup-Dienst aufräumen möchtest | Gmail-API-Konto, Safe-Mode und labelbasierte Bereinigung |
| Speicher in einem klassischen Postfach reduzieren möchtest | IMAP-Konto, Scanner für große Elemente und Papierkorb-Prüfung |
| alte Newsletter oder wiederkehrende Absender entfernen möchtest | Regel-Filter für Alter, Absender, Betreff und Ordner |
| verwandte Mail-Tools prüfen möchtest | [MailProcessor](https://github.com/doc-bricks/MailProcessor), [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber) und [UniversalInvoiceMail](https://github.com/doc-bricks/UniversalInvoiceMail) |

Geeignet für:

- Gmail-Bereinigung mit OAuth2 und Label-Aktionen
- IMAP-Mail-Aufräumen für GMX, Outlook, Gmail IMAP und weitere SSL-IMAP-Provider
- Suche nach großen E-Mails und optionalen Google-Drive-Dateien
- Geplante Safe-Mode-Bereinigung
- Lokales, datenschutzorientiertes Mail-Management unter Windows

## Funktionen

- Multi-Account-Management für IMAP-Provider plus Gmail API via OAuth2
- Die Google-Clientbibliotheken werden erst geladen, wenn wirklich ein
  Gmail-API-Konto authentifiziert wird; reine IMAP-Setups starten daher auch
  ohne die optionalen Gmail-Pakete
- Sichere Passwortspeicherung via `keyring` mit Fallback ohne Persistenz
- Regelbasierte Filter für Alter, Absender, Betreff und Größe
- Mehrordner-Support statt reiner INBOX-Verarbeitung
- Safe-Mode per Papierkorb und Unsafe-Mode für endgültiges Löschen
- Undo für Safe-Mode-Löschaktionen
- Scanner für große Elemente mit tabellarischer Auswahl für Gmail, IMAP und optionale Drive-Bereinigung
- Gmail-spezifische Tabs für Speicherstatistiken und labelbasiertes Aufräumen
- Konfigurierbares Logging über `UMAIL_CLEANER_LOG_LEVEL`
- Modulare Struktur mit `imap_client.py`, `models.py` und `workers.py`
- Secrets-freier Profil-Export/-Import für Regeln, Kontometadaten und Scheduler-Vorgaben

## Suchbegriffe

`doc-bricks/UniversalMailCleaner`, `UniversalMailCleaner`, `Gmail Cleaner`, `Gmail aufräumen`, `IMAP Cleaner`, `imap-cleaner`, `Mailbox Cleaner`, `Mailbox Cleanup`, `Postfach aufräumen`, `E-Mail-Bereinigung`, `große Mails finden`, `Gmail Labels aufräumen`, `lokales Mail-Management`, `PySide6 Desktop-App`, `Windows Mail Cleaner`, `sicheres E-Mail-Löschen`

## Suche und Abgrenzung

UniversalMailCleaner ist eine lokale Desktop-App für Mailbox-Bereinigung, kein E-Mail-Marketing-Tool, kein CRM, kein gehosteter Abmeldedienst, kein Mailinglisten-Validator, kein MailCleaner-Anti-Spam-Gateway und keine reine Browser-Erweiterung für Gmail. Das Repository passt am besten zu Suchanfragen nach `doc-bricks/UniversalMailCleaner`, lokaler Gmail-Bereinigung, IMAP-Mailbox-Cleaner, große Mails finden unter Windows, PySide6-Mailverwaltung, Postfach aufräumen ohne Abo, Safe-Mode-Mail-Cleanup und Gmail-Label-Bereinigung mit Undo.

## Start

### Windows

`START.bat` per Doppelklick ausführen

### Manuell

```bash
pip install -e .
universalmailcleaner
```

Legacy-Alternative:

```bash
pip install -r requirements.txt
python mail_imap_cleaner_v1.py
```

## Typischer Workflow

1. IMAP-Konto oder Gmail-API-Konto anlegen
2. Papierkorb-Ordner für IMAP-Konten prüfen oder auto-erkennen lassen
3. Regel definieren oder Scanner für große Elemente nutzen
4. Für Gmail-API-Konten bei Bedarf die Drive-Dateisuche aktivieren
5. Zielordner für IMAP-Regelläufe auswählen
6. Aktion im Safe-Mode ausführen
7. Falls nötig letzte Löschung rückgängig machen

## Konfiguration

- Lokale Konfigurationsdatei: `%USERPROFILE%\.mail_cleaner\config.json`
- Passwörter werden nicht in der JSON-Datei gespeichert
- Safe-Mode ist standardmäßig aktiv

## Tests

```bash
pytest tests -v
```

## Sicherheit

- IMAP läuft über verschlüsselte Verbindungen (`IMAP4_SSL`)
- Safe-Mode verschiebt Mails standardmäßig in den Papierkorb
- Undo steht für Safe-Mode-Aktionen zur Verfügung
- Ohne `keyring` werden Passwörter nur für die aktuelle Session gehalten

## Unterstützte Provider

- GMX (`imap.gmx.net:993`)
- Gmail via IMAP (`imap.gmail.com:993`) mit App-Passwort
- Gmail via Gmail API mit OAuth2 (`credentials.json` erforderlich)
- Outlook (`outlook.office365.com:993`)
- Weitere IMAP4-Provider mit Standard-SSL-Setup

## FAQ

**Gmail-Login schlägt fehl?**
Für IMAP: Zwei-Faktor-Authentifizierung aktivieren und ein App-Passwort erstellen:
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

Für Gmail API: `credentials.json` neben die Anwendung legen und den OAuth2-Login im Browser abschließen.
Die optionalen Google-Clientpakete werden nur für diesen Gmail-API-Pfad
benötigt; reine IMAP-Nutzung startet auch ohne sie.

Wenn nach einem Upgrade die Drive-Bereinigung nicht verfügbar bleibt, einmal
`%LOCALAPPDATA%\\UniversalMailCleaner\\gmail_token.json` löschen und den OAuth2-Login erneut ausführen, damit der neue Drive-Zugriff freigegeben wird.

**Keyring fehlt?**
Installation via `pip install keyring`.

**Papierkorb-Ordner nicht erkannt?**
Im Konto-Dialog manuell setzen.

## Verwandte Tools

Teil der [doc-bricks](https://github.com/doc-bricks) Mail-Suite:

| Tool | Beschreibung |
|------|--------------|
| [MailProcessor](https://github.com/doc-bricks/MailProcessor) | System-Tray-Launcher für alle Universal Mail Tools |
| [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber) | Dokumente und Anhänge aus IMAP-Mails herunterladen |
| [UniversalInvoiceMail](https://github.com/doc-bricks/UniversalInvoiceMail) | Rechnungen und Belege automatisch aus Mails extrahieren |

## Lizenz

[MIT](LICENSE)
