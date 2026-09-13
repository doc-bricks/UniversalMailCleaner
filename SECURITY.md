# Security Policy / Sicherheitsrichtlinie

## Deutsch

### Sicherheitsphilosophie & Leitlinien

`doc-bricks/UniversalMailCleaner` ist als rein lokale Windows-Desktop-Anwendung (PySide6) für die sichere Bereinigung und Verwaltung von IMAP- und Gmail-Postfächern konzipiert. Sicherheit, Datenschutz, Vertraulichkeit von Kommunikationsdaten und Ausfallsicherheit basieren auf folgenden Kernprinzipien:

- **Local-First & Zero-Egress (INV-LOCAL-01):** UniversalMailCleaner verarbeitet E-Mails, Filterregeln und Caches ausschließlich lokal auf dem Benutzerrechner. Es werden keinerlei Telemetriedaten, Nutzungsstatistiken, E-Mail-Inhalte oder Header an Drittanbieter-Cloud-Server übermittelt.
- **Verschlüsselte Zugangsdaten-Isolation (INV-CRED-02):** Passwörter und OAuth2-Tokens werden über `keyring` sicher in der Windows-Anmeldeinformationsverwaltung (Windows DPAPI) isoliert. Zugangsdaten werden niemals im Klartext in Konfigurationsdateien (`config.json`) gespeichert.
- **Sicherer Papierkorb-Standard (INV-SAFE-03):** Der Standard-Löschmodus verschiebt Nachrichten in den serverseitigen Papierkorb (`Trash`, `Papierkorb`, `[Gmail]/Trash`) unter Beachtung von `UIDVALIDITY` und `COPYUID`, anstatt sofortige permanente `EXPUNGE`-Befehle auszulösen.
- **Transaktionale Undo-Wiederherstellung (INV-UNDO-04):** Im sicheren Papierkorb-Modus registriert UniversalMailCleaner verschobene UIDs in einem flüchtigen Arbeitsspeicher-Puffer und ermöglicht die sofortige 1-Klick-Wiederherstellung in den ursprünglichen Ordner.
- **Explizite Bestätigung bei Permanentlöschung (INV-CONFIRM-05):** Das dauerhafte Löschen (`EXPUNGE`) erfordert eine explizite Bestätigung über einen Sicherheitsdialog mit eindeutigen Warnhinweisen.
- **Erzwungene TLS-Transportsicherheit (INV-TLS-06):** Netzwerkverbindungen erzwingen `IMAP4_SSL` (Port 993) sowie HTTPS / TLS 1.3 für Google APIs. Unverschlüsselte Klartextübertragungen sind ausgeschlossen.
- **Minimaler Berechtigungsumfang (Least-Privilege, INV-LEASTPRIV-07):** Google OAuth2 fordert ausschließlich minimale Arbeitsberechtigungen (`gmail.modify`, optional `drive.file` / `drive.metadata.readonly` für Speicherplatzscans) ohne administrative Kontenübernahmen an.
- **Lazy-Loading optionaler Abhängigkeiten (INV-LAZYLOAD-08):** Google-Client-Bibliotheken werden dynamisch geladen. Reine IMAP-Nutzer können die Anwendung ohne Google-Abhängigkeiten betreiben.
- **Geheimnisfreier Profil-Export (INV-PORTABLE-09):** Exportierte Bereinigungsregeln und Zeitplan-Profile (`profile_exchange.py`) bereinigen Passwörter und Tokens vollständig, sodass Profile sicher geteilt werden können.
- **Unprivilegierter User-Mode (Non-Elevation):** Die Anwendung benötigt und verlangt keine Administratorrechte.

### Unterstützte Versionen

| Version | Unterstützt | Anmerkungen |
| ------- | ----------- | ----------- |
| 1.2.x   | Ja          | Aktuelle Hauptversion mit Gmail/IMAP, Safe Trash, Undo & Scheduler |
| < 1.2.0 | Nein        | Bitte auf Version 1.2.0 oder höher aktualisieren |

### Sicherheitslücken melden

Wenn Sie eine Sicherheitslücke oder ein kritisches Problem in UniversalMailCleaner entdecken:

1. **Bevorzugter Meldeweg:** Nutzen Sie die private Vulnerability-Reporting-Funktion auf GitHub:
   - Öffnen Sie den Tab **Security** in diesem Repository
   - Wählen Sie **Report a vulnerability** ([Direktlink](https://github.com/doc-bricks/UniversalMailCleaner/security/advisories/new))
   - Beschreiben Sie das Verhalten, Schritte zur Reproduktion und mögliche Auswirkungen
2. **Direkter E-Mail-Kontakt:** Alternativ können Sie sich direkt an unsere Sicherheitskoordinatoren wenden:
   - `security@doc-bricks.org`
   - `security@open-bricks.org`
   - `security@ellmos.ai`
   - `support@lukasgeiger.com`
   - `lukas@open-bricks.org`

Bitte öffnen Sie für Sicherheitslücken **keine öffentlichen Issues** und veröffentlichen Sie keine E-Mail-Inhalte, Tokens oder Zugangsdaten.

### Reaktionszeit & SLA (INV-SLA-10)

Wir bestätigen den Eingang jeder Sicherheitsmeldung innerhalb von **48 Stunden** und streben eine erste Bewertung / Triage innerhalb von **5 Werktagen** an. Bestätigte Sicherheitsprobleme werden mit höchster Priorität behoben.

---

## English

### Security Principles & Core Guarantees

`doc-bricks/UniversalMailCleaner` is engineered as a strictly local Windows desktop application (PySide6) for safe cleanup and management of IMAP and Gmail mailboxes. Security, privacy, confidentiality of communications, and operational resiliency are grounded in the following core principles:

- **Local-First & Zero-Egress (INV-LOCAL-01):** UniversalMailCleaner processes all emails, rules, and cache files strictly on the user's local workstation. No telemetry, usage statistics, email bodies, or headers are transmitted to third-party cloud servers.
- **Encrypted Credential Isolation (INV-CRED-02):** Passwords and OAuth2 refresh tokens are securely stored in the Windows Credential Manager (Windows DPAPI) via `keyring`. Credentials are never written in plaintext to configuration files (`config.json`).
- **Safe-by-Default Deletion (INV-SAFE-03):** Default cleanup operations move messages to the server's designated trash folder (`Trash`, `Papierkorb`, `[Gmail]/Trash`) validating `UIDVALIDITY` and `COPYUID`, rather than issuing destructive `EXPUNGE` commands.
- **Transactional Undo Capability (INV-UNDO-04):** Safe-mode operations register moved message UIDs in an in-memory buffer, allowing immediate single-click reversal back to the source folder.
- **Explicit Hard-Delete Opt-In (INV-CONFIRM-05):** Permanent deletion (`EXPUNGE`) requires explicit confirmation via warning dialog.
- **Enforced TLS Transport Security (INV-TLS-06):** Network transport strictly requires `IMAP4_SSL` (port 993) and HTTPS / TLS 1.3 for Google APIs; unencrypted transport is rejected.
- **Least-Privilege OAuth2 Scopes (INV-LEASTPRIV-07):** Google OAuth2 requests only minimal necessary scopes (`gmail.modify`, optional `drive.file` / `drive.metadata.readonly` for storage audits) without administrative access.
- **Lazy Optional Dependency Boundary (INV-LAZYLOAD-08):** Google client libraries are imported dynamically on demand, allowing IMAP users to operate without Google dependencies.
- **Secrets-Free Profile Portability (INV-PORTABLE-09):** Exported rule and scheduler configurations (`profile_exchange.py`) strip all credentials and secrets, enabling safe cross-machine sharing and version control storage.
- **Unprivileged User-Mode Operation:** UniversalMailCleaner runs entirely within standard user privileges and never requires administrative elevation.

### Supported Versions

| Version | Supported | Notes |
| ------- | --------- | ----- |
| 1.2.x   | Yes       | Active production release with Gmail/IMAP, Safe Trash, Undo & Scheduler |
| < 1.2.0 | No        | Please upgrade to version 1.2.0 or higher |

### Reporting a Vulnerability

If you discover a security vulnerability or credential exposure in UniversalMailCleaner:

1. **Preferred Method:** Report privately via GitHub's Security Advisories flow:
   - Navigate to the **Security** tab of this repository
   - Click **Report a vulnerability** ([Direct Link](https://github.com/doc-bricks/UniversalMailCleaner/security/advisories/new))
   - Provide reproduction steps, affected environment, and potential impact
2. **Direct Security Email:** Alternatively, email our security coordinators directly:
   - `security@doc-bricks.org`
   - `security@open-bricks.org`
   - `security@ellmos.ai`
   - `support@lukasgeiger.com`
   - `lukas@open-bricks.org`

Please **do not disclose vulnerabilities in public issues**.

### Response Time & SLA (INV-SLA-10)

We acknowledge receipt of any security vulnerability report within **48 hours** and aim for an initial assessment and triage within **5 business days**. Confirmed security patches are prioritized and released promptly.
