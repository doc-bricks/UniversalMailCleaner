<img src="assets/banner.svg" width="100%" alt="UniversalMailCleaner Banner">

# UniversalMailCleaner

**🇬🇧 English** · **[🇩🇪 Deutsche Dokumentation](README_de.md)**

> Local-first Windows desktop app for cleaning IMAP and Gmail mailboxes — rule-based cleanup, large-mail scans, scheduler, safe trash mode.

[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-v1.2.0-blue)](CHANGELOG.md)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)](#start-here)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41cd52)](https://pypi.org/project/PySide6/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](pyproject.toml)
[![Tests: 81 Passed](https://img.shields.io/badge/Tests-81%20Passed-brightgreen)](tests)
[![Organization: doc-bricks](https://img.shields.io/badge/organization-doc--bricks-blue)](https://github.com/doc-bricks)
[![Ecosystem: open-bricks](https://img.shields.io/badge/ecosystem-open--bricks-blue)](https://github.com/open-bricks)
[![LLM-Ready](https://img.shields.io/badge/LLM--Ready-llms.txt-blue)](llms.txt)

> [!NOTE]
> Machine-readable repository summary for AI agents and LLMs available at [`llms.txt`](llms.txt).

UniversalMailCleaner combines rule-based email cleanup, large-mail and Drive scans, scheduler runs, safe trash mode, and undoable deletion workflows in one PySide6 interface.

![UniversalMailCleaner desktop mailbox cleanup UI with accounts, rules, large-item scan, Gmail labels, scheduler, and safe trash mode](README/screenshots/main.png)

## Why UniversalMailCleaner

UniversalMailCleaner is built for people who want to reduce mailbox storage and newsletter clutter without handing their inbox to another cloud service. It runs locally, keeps passwords out of the project config, supports standard IMAP providers, and can use the Gmail API when OAuth2 account features are needed.

## Architecture

```mermaid
graph TD
    UI["PySide6 MainWindow UI"] --> AC["Account Manager"]
    UI --> RL["Rules Engine"]
    UI --> LS["Large Mail & Drive Scanner"]
    UI --> SC["Scheduler (QTimer)"]
    UI --> ST["Safe Trash & Undo Manager"]

    AC --> KR["OS Keyring (Encrypted Credentials)"]
    RL --> WK["Background Worker Thread"]
    LS --> WK
    SC --> WK
    ST --> WK

    WK --> IMAP["ImapService (SSL IMAP4 / UIDPLUS)"]
    WK --> GMAIL["GmailService (OAuth2 & Drive API)"]

    IMAP --> SRV[("IMAP Mail Servers (GMX, Outlook, Gmail)")]
    GMAIL --> GOOG[("Google Mail & Drive APIs")]
```

## Start Here

| If you want to... | Start with |
|---|---|
| clean a Gmail inbox without a hosted cleanup service | Gmail API account, safe mode, and label-aware cleanup |
| reduce storage in a classic mailbox | IMAP account, large-item scanner, and trash-folder check |
| remove old newsletters or repetitive senders | rule filters for age, sender, subject, and folder |
| review related mail tools | [MailProcessor](https://github.com/doc-bricks/MailProcessor), [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber), and [UniversalInvoiceMail](https://github.com/doc-bricks/UniversalInvoiceMail) |

Use it for:

- Gmail mailbox cleanup with OAuth2 and label-aware actions
- IMAP email cleanup for GMX, Outlook, Gmail IMAP, and other SSL IMAP providers
- Large email and optional Google Drive file cleanup
- Scheduled safe-mode mailbox maintenance
- Local, privacy-conscious mail management on Windows

## Features

- Multi-account support for IMAP providers plus Gmail API via OAuth2
- Google client libraries are only loaded when a Gmail API account is authenticated, so IMAP-only setups start without optional dependencies
- Secure password storage via `keyring` with session-only fallback
- Rule-based filters for age, sender, subject, and size
- Multi-folder support beyond INBOX-only processing
- Safe mode (trash) plus unsafe mode for permanent deletion
- Undo for safe-mode deletions
- Large-item scanner with tabular selection for Gmail, IMAP, and optional Drive cleanup
- Gmail-specific tabs for storage statistics and label-based cleanup
- Secrets-free profile export/import for rules, account metadata, and scheduler presets
- Configurable logging via `UMAIL_CLEANER_LOG_LEVEL`
- Modular architecture: `imap_client.py`, `models.py`, `workers.py`, `profile_exchange.py`, `scheduler_widget.py`

## Discovery Keywords

`doc-bricks/UniversalMailCleaner`, `UniversalMailCleaner`, `gmail cleaner`, `gmail cleanup tool`, `imap cleaner`, `imap-cleaner`, `mailbox cleaner`, `mailbox cleanup`, `inbox cleanup`, `email cleanup`, `large email finder`, `gmail label cleanup`, `local-first email management`, `PySide6 desktop app`, `Windows email cleaner`, `safe delete email cleanup`

## Search and Disambiguation

UniversalMailCleaner is a desktop mailbox cleanup app, not an email marketing tool, CRM, hosted unsubscribe service, mailing-list validator, MailCleaner anti-spam gateway, or browser-only Gmail extension. The repository is best matched by searches for `doc-bricks/UniversalMailCleaner`, local-first Gmail cleanup, IMAP mailbox cleaner, large email finder for Windows, PySide6 email management app, safe trash mode mail cleanup, inbox cleanup without subscription, and Gmail label cleanup with undo support.

## Run

### Windows

Double-click `START.bat`

### Manual

```bash
pip install -e .
universalmailcleaner
```

Legacy alternative:

```bash
pip install -r requirements.txt
python mail_imap_cleaner_v1.py
```

## Typical Workflow

1. Add an IMAP account or a Gmail API account
2. Check or auto-detect the trash folder for IMAP accounts
3. Define a rule or use the large-item scanner
4. Enable Drive file scanning for Gmail API accounts if needed
5. Select the target folder for IMAP rule runs if needed
6. Execute in safe mode
7. Undo the last deletion if needed

## Configuration

- Config file: `%USERPROFILE%\.mail_cleaner\config.json`
- Passwords are not stored in the JSON file
- Safe mode is active by default

## Tests

```bash
pytest tests -v
```

## Safety

- IMAP uses encrypted connections (`IMAP4_SSL`)
- Safe mode moves mails to trash by default
- Undo available for all safe-mode actions
- Without `keyring`, passwords are held in the current session only

## Supported Providers

- GMX (`imap.gmx.net:993`)
- Gmail via IMAP (`imap.gmail.com:993`) with App Password
- Gmail via Gmail API account with OAuth2 (`credentials.json` required)
- Outlook (`outlook.office365.com:993`)
- Any IMAP4 provider with standard SSL

## FAQ

**Gmail login fails?**
For IMAP, enable two-factor authentication and create an App Password:
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

For Gmail API accounts, place `credentials.json` next to the application and complete the OAuth2 browser login.
The optional Google client packages are only required for this Gmail API path; pure IMAP usage starts without them.

If you upgrade from an older Gmail-only token and Drive cleanup stays unavailable, delete `%LOCALAPPDATA%\UniversalMailCleaner\gmail_token.json` once and authenticate again so the new Drive scope can be granted.

**Keyring is missing?**
Install via `pip install keyring`.

**Trash folder not detected?**
Set it manually in the account dialog.

## Ecosystem & Sibling Tools

UniversalMailCleaner is part of the **doc-bricks** document and productivity tools family, under the **open-bricks** ecosystem umbrella:

| Tool | Focus & Purpose | Status |
|---|---|---|
| [MailProcessor](https://github.com/doc-bricks/MailProcessor) | System tray launcher and orchestrator for all Universal Mail Tools | Production |
| [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber) | Rule-based attachment and document extraction from IMAP mailboxes | Production |
| [UniversalInvoiceMail](https://github.com/doc-bricks/UniversalInvoiceMail) | Automated invoice and receipt retrieval and sorting from email | Production |
| [DokuZen](https://github.com/doc-bricks/DokuZen) | Local document and PDF management suite (22 tools in PySide6) | Production |
| [PDFtoPDFocr](https://github.com/doc-bricks/PDFtoPDFocr) | Optical character recognition (OCR) desktop app for scanned PDFs | Production |
| [MediaBrain](https://github.com/doc-bricks/MediaBrain) | Multi-format media and document metadata analyzer and converter | Production |
| [ProFiler](https://github.com/file-bricks/ProFiler) | Fast desktop file management, organization, and batch workflow tool | Production |

## License

[MIT](LICENSE)
