# Third-Party Licenses & Dependency Inventory

**Project:** UniversalMailCleaner (`doc-bricks/UniversalMailCleaner`)<br>
**Canonical Project License:** MIT License (`MIT`)<br>
**Audit Date:** 2026-10-03 (Pfad B Discoverability & Architecture; Previous: 2026-10-01, 2026-09-26, 2026-09-22)<br>
**Auditor:** Antigravity / Gemini (via GithubBot Pfad B)<br>
**Version:** `1.2.0`<br>
**Umbrella Ecosystem:** `open-bricks` / `doc-bricks`<br>
**Notice Attribution:** See canonical root [`NOTICE`](NOTICE) file.

---

## 1. Overview & Compliance Architecture

UniversalMailCleaner is an open-source, local-first Windows desktop application for managing, filtering, and cleaning IMAP and Gmail mailboxes. The application is licensed under the permissive **MIT License**. All direct runtime libraries, transitive packages, and development toolchains have been cataloged and audited for license compatibility, non-infringement, security vulnerability floors, and strict local execution guarantees. Canonical attribution is declared in the root [`NOTICE`](NOTICE) file.

This inventory is derived directly from `pyproject.toml`, `requirements.txt`, and runtime dependency inspection.

### 10 Governance- & Runtime-Invarianten

| Invariant Code | Category | Name & Guarantee | Verification Boundary |
|---|---|---|---|
| `INV-LOCAL-01` | Architecture | **100% Local-First Execution** | All mailbox processing, filtering rules, and cache files remain entirely local; zero external telemetry or cloud analytics. |
| `INV-CRED-02` | Security | **Encrypted Credential Isolation** | Account passwords and tokens are held via `keyring` in the OS Credential Manager (Windows DPAPI) or session memory; never stored in plaintext `config.json`. |
| `INV-SAFE-03` | Safety | **Safe-by-Default Deletion** | Default operational mode routes all deletions to the provider's trash folder (`Trash`, `Papierkorb`, `[Gmail]/Trash`) rather than issuing immediate expunge commands. |
| `INV-UNDO-04` | Transaction | **Transactional Undo Capability** | Safe-mode deletions register message UIDs and folder mappings into an in-memory undo buffer, allowing immediate restoration. |
| `INV-CONFIRM-05` | Safety | **Explicit Hard-Delete Opt-In** | Permanent purge (`EXPUNGE`) requires explicit user confirmation via dialog modal with warning. |
| `INV-TLS-06` | Network | **Enforced TLS Transport Security** | Network communication strictly requires `IMAP4_SSL` (port 993) and TLS 1.3 / HTTPS for Google APIs; unencrypted plaintext transport is rejected. |
| `INV-LEASTPRIV-07` | Permission | **Least-Privilege OAuth2 Scopes** | Google OAuth2 asks only for minimal required scopes (`gmail.modify`, optional `drive.file` / `drive.metadata.readonly`); no admin or whole-account takeovers. |
| `INV-LAZYLOAD-08` | Runtime | **Lazy Optional Dependency Boundary** | Google client libraries (`google-api-python-client`, `google-auth-oauthlib`) are loaded lazily on demand; IMAP-only users start with zero Google library overhead. |
| `INV-PORTABLE-09` | Portability | **Secrets-Free Profile Portability** | Exported rule profiles (`profile_exchange.py`) strip all credentials and secrets, enabling safe cross-machine sharing and version-control storage. |
| `INV-SLA-10` | Governance | **48h Security SLA & 5-Day Triage** | Documented response timeline in `SECURITY.md` committing to 48-hour response and 5-day triage for all reported security vulnerabilities. |

---

## 2. Direct Runtime Dependencies

| Package | Declared Constraint | SPDX License | Upstream Project / Repository | Compatibility Analysis |
|---|---|---|---|---|
| **PySide6** | `>=6.5.0,<7.0.0` | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` | [The Qt Company](https://doc.qt.io/qtforpython-6/) | **Weak Copyleft / Permissive**: Dynamic linking under LGPL-3.0 is compatible with MIT-licensed host software without viral license contagion. |
| **keyring** | `>=23.0.0,<26.0.0` | `MIT` | [jaraco/keyring](https://github.com/jaraco/keyring) | **Permissive**: Fully compatible with MIT. Provides native Windows DPAPI credential protection. |
| **google-auth-oauthlib** | `>=1.0.0,<2.0.0` | `Apache-2.0` | [Google Auth Library](https://github.com/googleapis/google-auth-library-python-oauthlib) | **Permissive**: Apache-2.0 is compatible with MIT applications. Optional path for OAuth2 browser authentication. |
| **google-api-python-client** | `>=2.0.0,<3.0.0` | `Apache-2.0` | [Google API Python Client](https://github.com/googleapis/google-api-python-client) | **Permissive**: Apache-2.0 is compatible with MIT applications. Optional path for Gmail API & Drive API interaction. |

---

## 3. Transitive Runtime Dependencies

| Package | SPDX License | Parent Dependency | Purpose |
|---|---|---|---|
| **PySide6_Essentials** | `LGPL-3.0-only` | PySide6 | Core Qt modules (QtCore, QtGui, QtWidgets, QtNetwork) |
| **PySide6_Addons** | `LGPL-3.0-only` | PySide6 | Extended Qt modules |
| **shiboken6** | `LGPL-3.0-only` | PySide6 | C++/Python binding generator runtime |
| **pywin32-ctypes** | `BSD-3-Clause` | keyring | Native Windows DPAPI / Credential Vault bridge |
| **jaraco.classes** | `MIT` | keyring | Class utilities |
| **jaraco.context** | `MIT` | keyring | Context manager utilities |
| **jaraco.functools** | `MIT` | keyring | Functional programming helpers |
| **more-itertools** | `MIT` | jaraco.functools | Extended iterator algorithms |
| **google-auth** | `Apache-2.0` | google-auth-oauthlib | Core Google authentication library |
| **google-auth-httplib2** | `Apache-2.0` | google-api-python-client | HTTP transport adapter for Google Auth |
| **google-api-core** | `Apache-2.0` | google-api-python-client | Shared API client utilities |
| **googleapis-common-protos** | `Apache-2.0` | google-api-core | Common protocol buffer definitions |
| **httplib2** | `MIT` | google-auth-httplib2 | HTTP client library |
| **requests-oauthlib** | `ISC` | google-auth-oauthlib | OAuthlib adapter for Requests |
| **oauthlib** | `BSD-3-Clause` | requests-oauthlib | Generic OAuth request-signing logic |
| **uritemplate** | `BSD-3-Clause OR Apache-2.0` | google-api-python-client | URI template expansion (RFC 6570) |
| **cryptography** | `Apache-2.0 OR BSD-3-Clause` | google-auth | Cryptographic primitives & certificates |
| **cffi** | `MIT` | cryptography | C Foreign Function Interface |
| **pycparser** | `BSD-3-Clause` | cffi | C parser in Python |
| **proto-plus** | `Apache-2.0` | google-api-core | Pythonic Protocol Buffers |
| **protobuf** | `BSD-3-Clause` | googleapis-common-protos | Google Protocol Buffers serialization |
| **requests** | `Apache-2.0` | requests-oauthlib | HTTP client library |
| **certifi** | `MPL-2.0` | requests | Mozilla CA certificate bundle |
| **charset-normalizer** | `MIT` | requests | Character encoding detection |
| **idna** | `BSD-3-Clause` | requests | Internationalized Domain Names in Applications |
| **urllib3** | `MIT` | requests | HTTP connection pool |

---

## 4. Development, Testing & Build Toolchain

| Package | Declared Constraint | SPDX License | Purpose | Compliance Status |
|---|---|---|---|---|
| **pytest** | `>=8.0` | `MIT` | Unit, integration & metadata contract testsuite | Permissive development tool. |
| **ruff** | `>=0.5` | `MIT OR Apache-2.0` | High-performance Python linter & code formatter | Permissive development tool. |
| **PyInstaller** | `>=6.0` | `GPL-2.0-or-later WITH Bootloader-Exception` | Windows standalone executable creation (`build_exe.bat`) | Bootloader exception explicitly permits distributing proprietary/MIT applications. |

---

## 5. Native Operating System Services & Standard Library

| Component | License | Purpose | Boundary Guarantee |
|---|---|---|---|
| **Python Standard Library** | `PSF-2.0` | Core logic (`imaplib`, `ssl`, `email`, `sqlite3`, `pathlib`, `json`, `threading`, `logging`) | Standard runtime provided by Python foundation. |
| **Windows Credential Manager** | Proprietary Microsoft API | Encrypted credential persistence via DPAPI | Operating system subsystem accessed via `keyring` WinVault. |
| **Windows Task Scheduler** | Operating System Feature | Optional background execution trigger | Managed natively by Windows. |

---

## 6. Supply Chain Governance & Verification

1. **Clean Worktree Requirement:** All released code must originate from a clean `master` branch with 100% green tests.
2. **Zero Plaintext Secret Storage:** Passwords, app tokens, and OAuth refresh tokens must never be written to JSON config files or logs.
3. **Lazy Dependency Isolation:** The application must remain fully functional for all standard IMAP providers without requiring Google client libraries to be installed or initialized.
4. **Vulnerability Defense:** Pinned minimum version floors eliminate known CVEs across transitive packages.
5. **Unprivileged User Mode / RunAsInvoker (`INV-USER-02`):** UniversalMailCleaner executes entirely in unprivileged standard user mode without requiring Administrator elevation, UAC prompts, or ring-0 drivers.

---

## 7. Level 1 SBOM Invariant Cross-Reference Matrix

| Invariant Code | Core Invariant Guarantee | Primary Verification Boundary | Runtime Defense / Mitigation |
|---|---|---|---|
| `INV-LOCAL-01` | 100% Local-First Execution | `mail_imap_cleaner_v1.py` | Localhost processing only; zero outbound analytics, metrics, or cloud telemetry. |
| `INV-CRED-02` | Encrypted Credential Isolation | `imap_client.py`, `keyring` | Windows DPAPI / OS Credential Vault; passwords never written to plaintext disk config. |
| `INV-SAFE-03` | Safe-by-Default Deletion | `workers.py` | Messages routed to server trash folder instead of issuing immediate hard expunge. |
| `INV-UNDO-04` | Transactional Undo Capability | `workers.py`, `mail_imap_cleaner_v1.py` | In-memory UID mapping buffer tracks trash relocations for one-click rollback. |
| `INV-CONFIRM-05` | Explicit Hard-Delete Opt-In | `mail_imap_cleaner_v1.py` | Permanent purge requires explicit user modal confirmation with warning dialog. |
| `INV-TLS-06` | Enforced TLS Transport Security | `imap_client.py` | SSL/TLS forced (`IMAP4_SSL`, port 993) and HTTPS OAuth endpoints; unencrypted links rejected. |
| `INV-LEASTPRIV-07` | Least-Privilege OAuth2 Scopes | `gmail_service.py` | Minimal scopes requested (`gmail.modify`); full admin access or wider account takeovers avoided. |
| `INV-LAZYLOAD-08` | Lazy Optional Dependency Boundary | `gmail_service.py` | Google client modules imported on-demand; zero startup overhead for standard IMAP accounts. |
| `INV-PORTABLE-09` | Secrets-Free Profile Portability | `profile_exchange.py` | Profile import/export strips all credentials; safe for version control and cross-machine sync. |
| `INV-SLA-10` | 48h Security SLA & 5-Day Triage | `SECURITY.md` | Documented 48-hour response and 5-day triage commitment with defined escalation channels. |
