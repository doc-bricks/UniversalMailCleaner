# Known Bugs and Design Limitations

## Open

### IMAP-001 — `undo_delete` uses scan-time sequence numbers against trash folder

**Severity:** Medium  
**File:** `workers.py`, lines 308-314 (`undo_delete`)  
**Status:** Open — requires larger refactor

**Description:**  
When the IMAP safe-mode delete path executes, it copies messages to the trash folder and then issues `EXPUNGE` on the original folder. After `EXPUNGE`, the sequence numbers recorded during the scan are no longer valid in the context of the trash folder (IMAP sequence numbers are relative to the current mailbox and shift after expunge). `undo_delete` later issues `COPY` and `STORE` commands against the trash folder using the old scan-time sequence numbers, which may address the wrong messages or fail silently.

**Root cause:**  
The scan, delete, and undo chain passes `item["id"]` (the original folder sequence number) through all three stages. UID-based addressing (`UID COPY`, `UID STORE`) would be stable across expunge and folder switches, but requires changes to `ImapService.get_messages`, `WorkerThread.scan_large`, `WorkerThread.delete_items`, and `WorkerThread.undo_delete`.

**Fix required:**  
Migrate the entire scan→delete→undo chain from sequence-number IDs to UIDs:
1. Use `UID SEARCH` / `UID FETCH` in `ImapService.get_messages` to store UIDs in `item["id"]`.
2. Issue `UID COPY`, `UID STORE \Deleted`, `UID EXPUNGE` (or `EXPUNGE` after UID-flagging) in `delete_items`.
3. Store the UID in the trash folder after the copy for use in `undo_delete`.
4. Use `UID COPY` and `UID STORE` in `undo_delete` against the trash folder.

## Resolved

### IMAP-002 — `get_search_criteria` generates wildcard queries for empty or non-positive values

**Severity:** High
**File:** `imap_client.py`, lines 191-208 (`get_search_criteria`)
**Status:** Resolved (2026-08-14)

**Description:**
Empty or whitespace-only values for `sender` and `subject` rules produced `(FROM "")` and `(SUBJECT "")`, which per RFC 3501 match all emails in the selected folder. Similarly, `older_than_days <= 0` produced past/future boundary searches, and `size_mb <= 0` generated `(LARGER 0)` matching all messages.

**Fix:**
Added input validation guards returning `None` for empty/whitespace filter values, `older_than_days <= 0`, and `size_mb <= 0`. Safely handled `[None]` data payloads in `workers.py` search processing. Added 6 unit tests in `tests/test_imap_service.py` and `tests/test_workers.py`.
