# UniversalMailCleaner

Desktop tool for cleaning IMAP mailboxes with rule-based filters, safe trash mode, multi-folder support, and undo for trash operations.

> **Deutsche Dokumentation:** [README-DE.md](README-DE.md)

![UniversalMailCleaner Preview](README/screenshots/main.png)

## Features

- Multi-account IMAP support for GMX, Gmail, and Outlook
- Secure password storage via `keyring` with session-only fallback
- Rule-based filters for age, sender, subject, and size
- Multi-folder support beyond INBOX-only processing
- Safe mode (trash) plus unsafe mode for permanent deletion
- Undo for safe-mode deletions
- Large-mail scanner with tabular selection
- Configurable logging via `UMAIL_CLEANER_LOG_LEVEL`
- Modular architecture: `imap_client.py`, `models.py`, `workers.py`

## Run

### Windows

Double-click `START.bat`

### Manual

```bash
pip install -r requirements.txt
python mail_imap_cleaner_v1.py
```

## Typical Workflow

1. Add an IMAP account
2. Check or auto-detect the trash folder
3. Define a rule or use the large-mail scanner
4. Select the target folder
5. Execute in safe mode
6. Undo the last deletion if needed

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
- Gmail (`imap.gmail.com:993`) with App Password
- Outlook (`outlook.office365.com:993`)
- Any IMAP4 provider with standard SSL

## FAQ

**Gmail login fails?**
Enable two-factor authentication and create an App Password at
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

**Keyring is missing?**
Install via `pip install keyring`.

**Trash folder not detected?**
Set it manually in the account dialog.

## Related Tools

Part of the [doc-bricks](https://github.com/doc-bricks) mail suite:

| Tool | Description |
|------|-------------|
| [MailProcessor](https://github.com/doc-bricks/MailProcessor) | System tray launcher for all Universal Mail Tools |
| [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber) | Download documents and attachments from IMAP mail |
| [UniversalInvoiceMail](https://github.com/doc-bricks/UniversalInvoiceMail) | Extract invoices and receipts from IMAP mail |

## License

[MIT](LICENSE)
