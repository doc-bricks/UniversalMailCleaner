# Beitragsrichtlinie / Contributing Guide

**UniversalMailCleaner** (`doc-bricks/UniversalMailCleaner`) · Part of the `open-bricks` ecosystem.

---

## English

Thank you for your interest in contributing to **UniversalMailCleaner**!

### Core Invariants & Architectural Principles

All contributions must strictly respect our 10 core governance and runtime invariants:

1. **100% Local-First Execution (`INV-LOCAL-01`)**: All mailbox processing, filtering rules, and cache files remain entirely local; zero external telemetry or cloud analytics.
2. **Encrypted Credential Isolation (`INV-CRED-02`)**: Account passwords and tokens are held via `keyring` in the OS Credential Manager (Windows DPAPI) or session memory; never stored in plaintext `config.json`.
3. **Safe-by-Default Deletion (`INV-SAFE-03`)**: Default operational mode routes all deletions to the provider's trash folder (`Trash`, `Papierkorb`, `[Gmail]/Trash`) rather than issuing immediate expunge commands.
4. **Transactional Undo Capability (`INV-UNDO-04`)**: Safe-mode deletions register message UIDs and folder mappings into an in-memory undo buffer, allowing immediate restoration.
5. **Explicit Hard-Delete Opt-In (`INV-CONFIRM-05`)**: Permanent purge (`EXPUNGE`) requires explicit user confirmation via dialog modal with safety warnings.
6. **Enforced TLS Transport Security (`INV-TLS-06`)**: Network communication strictly requires `IMAP4_SSL` (port 993) and TLS 1.3 / HTTPS for Google APIs; unencrypted plaintext transport is rejected.
7. **Least-Privilege OAuth2 Scopes (`INV-LEASTPRIV-07`)**: Google OAuth2 asks only for minimal required scopes (`gmail.modify`, optional `drive.file` / `drive.metadata.readonly`); no admin or whole-account takeovers.
8. **Lazy Optional Dependency Boundary (`INV-LAZYLOAD-08`)**: Google client libraries (`google-api-python-client`, `google-auth-oauthlib`) are loaded lazily on demand; IMAP-only users start with zero Google library overhead.
9. **Secrets-Free Profile Portability (`INV-PORTABLE-09`)**: Exported rule profiles (`profile_exchange.py`) strip all credentials and secrets, enabling safe cross-machine sharing and version-control storage.
10. **48h Security SLA & 5-Day Triage (`INV-SLA-10`)**: Documented response timeline in `SECURITY.md` committing to 48-hour response and 5-day triage for all reported security vulnerabilities.

### Unprivileged User Execution / RunAsInvoker (`INV-USER-02`)

UniversalMailCleaner operates entirely in standard user mode (`RunAsInvoker`). Contributions must never introduce requirements for Administrator UAC elevation, system driver installation, or privileged registry access.

### Strict Version Freeze Discipline

Under policy `T-20260920-167562623`, the current version `1.2.0` is strictly frozen. Routine hygiene, CI matrix, and documentation changes must not bump version numbers; all updates are recorded under `## [Unreleased]` in `CHANGELOG.md`.

### Plan D Local Development Workflow

All code modifications and testing must be executed in local Git clones (`C:\_Local_DEV\repos\...`). Cloud storage folders (e.g. OneDrive) serve only as gitless multi-device mirrors and must not be used for direct development.

### Development Setup & Quality Gates

```bash
# Clone the repository
git clone https://github.com/doc-bricks/UniversalMailCleaner.git
cd UniversalMailCleaner

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies in editable mode with development tools
pip install -e .[dev]

# Run full Pytest test suite
pytest

# Run Ruff linter and code formatting check
ruff check .

# Check Python bytecode compilation
python -m compileall -q .

# Verify git whitespace hygiene
git diff --check
```

---

## Deutsch

Vielen Dank für Ihr Interesse, zu **UniversalMailCleaner** beizutragen!

### Kern-Invarianten & Architektur-Prinzipien

Jeder Beitrag muss unsere 10 Governance- und Laufzeit-Invarianten verbindlich wahren:

1. **100% Local-First (`INV-LOCAL-01`)**: Keine Telemetrie, keine Tracking-Dienste, rein lokale Verarbeitung.
2. **Verschlüsselte Zugangsdaten (`INV-CRED-02`)**: Passwörter liegen im Windows Credential Manager (DPAPI via `keyring`), niemals im Klartext.
3. **Sicherheits-Papierkorbmodus (`INV-SAFE-03`)**: Standardmäßig Verschieben in den Papierkorb statt dauerhaftem Löschen.
4. **Transaktionales Undo (`INV-UNDO-04`)**: Wiederherstellbarkeit gelöschter Nachrichten über UID-Mapppings.
5. **Explizite Lösch-Bestätigung (`INV-CONFIRM-05`)**: Endgültiges Löschen erfordert gesonderte Nutzerbestätigung.
6. **Erzwungenes TLS (`INV-TLS-06`)**: Ausschließlich verschlüsselte Verbindungen (IMAP-SSL Port 993, HTTPS).
7. **Minimalprivilegien (`INV-LEASTPRIV-07`)**: Minimale OAuth2-Scopes für Google-Dienste.
8. **Lazy Loading (`INV-LAZYLOAD-08`)**: Optionale Google-Bibliotheken werden erst bei Bedarf geladen.
9. **Geheimnisfreier Profilaustausch (`INV-PORTABLE-09`)**: Exportierte Profile enthalten keine Zugangsdaten.
10. **48h Sicherheits-SLA (`INV-SLA-10`)**: Verbindliche Reaktionszeiten bei Sicherheitsmeldungen.

### Unprivilegierter Modus / RunAsInvoker (`INV-USER-02`)

Die Anwendung läuft vollständig im unprivilegierten Standard-Benutzermodus ohne Administratorrechte.

### Version-Freeze-Disziplin (T-20260920-167562623)

Die Version `1.2.0` bleibt eingefroren. Alle Änderungen werden unter `## [Unreleased]` im `CHANGELOG.md` erfasst.
