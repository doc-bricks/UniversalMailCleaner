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

**Note:** The existing test `test_undo_restores_messages_for_imap_backend` passes because the fake connection does not model sequence-number semantics. The test is a structural regression guard, not a protocol-correctness check.
