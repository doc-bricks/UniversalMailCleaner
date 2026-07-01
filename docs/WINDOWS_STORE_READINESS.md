# Windows Store Readiness

Stand: 2026-07-01

UniversalMailCleaner bleibt eine lokale Windows-Desktop-App. Dieser Store-Pfad ist ein Desktop-Bridge/MSIX-Pfad, kein Cloud-Maildienst und keine mobile Voll-App.

## Aktueller Status

- Store-Preflight-Skript: `python scripts/check_store_readiness.py --allow-blockers`
- Maschinenlesbar: `python scripts/check_store_readiness.py --json --allow-blockers`
- Store-Metadaten: `store_package.json`
- Lokale Desktop-Konfiguration: `%LOCALAPPDATA%\UniversalMailCleaner\config.json`
- Gmail-OAuth-Token: `%LOCALAPPDATA%\UniversalMailCleaner\gmail_token.json`
- Legacy-Lesefallback: `%USERPROFILE%\.mail_cleaner\config.json`

## Geklärte Punkte

- Passwörter werden nicht in der JSON-Konfiguration gespeichert.
- `credentials.json`, OAuth-Tokens, Datenbanken, Schlüsseldateien und Release-Artefakte sind in `.gitignore` ausgeschlossen.
- Gmail-Tokens werden nicht im Installationsordner abgelegt.
- Bestehende Installationen können die alte `~/.mail_cleaner/config.json` noch lesen; neue Saves schreiben in den Store-freundlichen `%LOCALAPPDATA%`-Pfad.
- Web/PWA bleibt read-only und führt keine IMAP-, Gmail-, Drive- oder Löschaktionen aus.

## Externe Blocker

- Partner-Center-Publisher-DN in `store_package.json` ersetzen.
- Öffentliche Privacy- und Support-URLs eintragen.
- MSIX mit der echten Publisher-Identität bauen.
- WACK als Administrator gegen das MSIX ausführen und XML-Report unter `releases/windowsstore/` ablegen.
- Store-Screenshots müssen die Safe-Mode-/Undo-Grenzen sichtbar machen.

## Release-Grenzen

Nicht in Store- oder Release-Artefakte aufnehmen:

- `credentials.json`
- `client_secret*.json`
- `token.json` / `gmail_token.json`
- lokale Mailbox-Datenbanken oder Exportdaten
- `.env`, Schlüsseldateien, Logs und Backup-Ordner
