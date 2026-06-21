# UniversalMailCleaner Web Companion

Read-only mobile/browser companion for `universalmailcleaner-profile-v1.json`.

## Scope

- Local JSON import from the desktop export
- Optional JSON paste for quick sharing between devices
- Offline cache of the last loaded secrets-free profile
- Account, rule, scheduler, and scan-setting overview
- No IMAP, Gmail API, OAuth, Drive, or destructive cleanup actions

## Local start

From the project root:

```powershell
python -m http.server 4178 -d web_companion
```

Then open:

```text
http://127.0.0.1:4178/
```

## Companion contract

The companion expects the schema documented in the project root:

- [`../EXPORTFORMAT.md`](../EXPORTFORMAT.md)
- Schema: `universalmailcleaner-profile-v1`

The last loaded payload is stored in browser `localStorage` only. Credentials,
tokens, message IDs, Drive IDs, and deletion logs remain desktop-only and are
not part of the companion contract.
