"""Background worker thread for Universal Mail Cleaner.

Contains the Worker QThread class for IMAP and Gmail API operations.
"""

import email
import logging
import imaplib
from typing import List

from PySide6.QtCore import QThread, Signal

from gmail_service import GmailService
from imap_client import ImapService, decode_header_str
from models import MailAccount

APP_NAME = "MailCleaner_V8_Universal"
logger = logging.getLogger(APP_NAME)


class Worker(QThread):
    """Background worker for IMAP and Gmail API operations (QThread).

    Executes time-intensive mail tasks (rules, scanning, deleting) in a
    separate thread to keep the GUI responsive.

    Signals:
        log (str): Log message for the GUI.
        data_ready (list): Data for the GUI (e.g. large emails).
        finished (str): Completion message.
    """

    log = Signal(str)
    data_ready = Signal(list)
    finished = Signal(str)

    def __init__(self, mode: str, params: dict, accounts: List[MailAccount]) -> None:
        """Initializes the worker.

        Args:
            mode: "rules", "scan_large", "delete", or "undo".
            params: Parameters for the selected mode.
            accounts: List of MailAccount objects.
        """
        super().__init__()
        self.mode = mode
        self.params = params
        self.accounts = accounts
        self.service = None
        self.safe_mode = params.get("safe_mode", True)

    def run(self) -> None:
        """Main loop of the worker (called automatically by QThread)."""
        target_acc_name = self.params.get("target_account", "Alle")
        to_process = (
            self.accounts
            if target_acc_name == "Alle"
            else [a for a in self.accounts if a.name == target_acc_name]
        )

        if not to_process:
            self.log.emit("No account selected.")
            self.finished.emit("Aborted.")
            return

        for acc in to_process:
            if self.isInterruptionRequested():
                break

            self.service = self._connect_service(acc)
            if self.service is None:
                continue

            try:
                if self.mode == "rules":
                    self.run_rules(acc)
                elif self.mode == "scan_large":
                    self.scan_large(acc)
                elif self.mode == "delete":
                    self.delete_items(acc)
                elif self.mode == "undo":
                    self.undo_delete(acc)
            except Exception as exc:  # noqa: BLE001
                self.log.emit(f"Runtime error for {acc.name}: {exc}")
            finally:
                if isinstance(self.service, ImapService):
                    self.service.disconnect()

        self.finished.emit("Operation completed.")

    def _connect_service(self, acc: MailAccount):
        """Create and authenticate the backend service for one account."""
        if getattr(acc, "protocol", "IMAP") == "Gmail API":
            service = GmailService(log_func=self.log.emit)
            if not service.auth():
                self.log.emit(f"Gmail OAuth failed for {acc.name}.")
                return None
            self.log.emit(f"Gmail API connected for {acc.user or acc.name}.")
            return service

        service = ImapService(self.log.emit)
        if not service.connect(acc):
            return None
        return service

    def run_rules(self, acc: MailAccount) -> None:
        """Executes automatic cleanup rules on an account."""
        rules = self.params.get("rules", [])

        if getattr(acc, "protocol", "IMAP") == "Gmail API":
            self._run_gmail_rules(acc, rules)
            return

        trash_folder = self.service.find_trash_folder()
        folders = self.params.get("folders", ["INBOX"])

        for folder in folders:
            if self.isInterruptionRequested():
                break
            try:
                self.service.conn.select(folder)
                self.log.emit(f"Folder: {folder}")
            except Exception as exc:  # noqa: BLE001
                self.log.emit(f"Cannot select folder '{folder}': {exc}")
                continue

            for rule in rules:
                if self.isInterruptionRequested():
                    break
                if rule.target_account not in ["Alle", acc.name]:
                    continue
                if not rule.active:
                    continue

                criteria = self.service.get_search_criteria(rule)
                if not criteria:
                    continue

                self.log.emit(f"Rule '{rule.name}' on {acc.name}/{folder}...")
                typ, data = self.service.conn.search(None, criteria)

                if typ != "OK":
                    continue

                ids = data[0].split()
                if not ids:
                    self.log.emit("   No matches.")
                    continue

                self.log.emit(f"   Found {len(ids)} emails. Processing...")
                id_str = b",".join(ids).decode()

                try:
                    if self.safe_mode:
                        copy_result = self.service.conn.copy(id_str, trash_folder)
                        if copy_result[0] == "OK":
                            self.service.conn.store(id_str, "+FLAGS", "\\Deleted")
                            self.service.conn.expunge()
                            self.log.emit("   Moved to trash.")
                        else:
                            self.log.emit(f"   Could not move to trash: {copy_result}")
                    else:
                        self.service.conn.store(id_str, "+FLAGS", "\\Deleted")
                        self.service.conn.expunge()
                        self.log.emit("   Permanently deleted.")
                except imaplib.IMAP4.error as exc:
                    self.log.emit(f"   IMAP error during deletion: {exc}")
                except Exception as exc:  # noqa: BLE001
                    self.log.emit(f"   Unexpected error: {exc}")

    def _run_gmail_rules(self, acc: MailAccount, rules) -> None:
        """Execute cleanup rules against a Gmail API account."""
        for rule in rules:
            if self.isInterruptionRequested():
                break
            if rule.target_account not in ["Alle", acc.name]:
                continue
            if not rule.active:
                continue

            self.log.emit(f"Rule '{rule.name}' on {acc.name}...")
            processed = self.service.process_rule(rule, trash=self.safe_mode)
            if processed:
                if self.safe_mode:
                    self.log.emit("   Moved to trash.")
                else:
                    self.log.emit("   Permanently deleted.")

    def scan_large(self, acc: MailAccount) -> None:
        """Scans an account for large emails."""
        if getattr(acc, "protocol", "IMAP") == "Gmail API":
            self._scan_large_gmail(acc)
            return
        if not self.params.get("scan_mail", True):
            return

        threshold_mb = self.params.get("threshold", 10)
        limit_bytes = int(threshold_mb * 1024 * 1024)
        folders = self.params.get("folders", ["INBOX"])

        self.log.emit(f"Scanning {acc.name} for emails > {threshold_mb}MB...")
        results = []

        for folder in folders:
            if self.isInterruptionRequested():
                break
            try:
                self.service.conn.select(folder, readonly=True)
            except Exception as exc:  # noqa: BLE001
                self.log.emit(f"Cannot select folder '{folder}': {exc}")
                continue

            typ, data = self.service.conn.search(None, f"(LARGER {limit_bytes})")
            if typ != "OK":
                continue

            ids = data[0].split()
            ids = ids[-50:]

            for num in ids:
                if self.isInterruptionRequested():
                    break
                try:
                    _res, fetch_data = self.service.conn.fetch(
                        num, "(RFC822.SIZE BODY.PEEK[HEADER.FIELDS (SUBJECT DATE)])"
                    )

                    size_bytes = 0
                    subject = "Unknown"
                    date_str = ""

                    for response_part in fetch_data:
                        if not isinstance(response_part, tuple):
                            continue
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_header_str(msg["Subject"])
                        date_str = (msg["Date"] or "")[:16]

                        meta = response_part[0].decode()
                        if "RFC822.SIZE" in meta:
                            parts = meta.split("RFC822.SIZE")
                            if len(parts) > 1:
                                size_bytes = int(
                                    parts[1].strip().split()[0].replace(")", "")
                                )

                    if size_bytes > 0:
                        results.append({
                            "account": acc.name,
                            "folder": folder,
                            "id": num.decode(),
                            "subject": subject,
                            "size": size_bytes / (1024 * 1024),
                            "date": date_str,
                        })
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "scan_large: error fetching email %s in %s: %s",
                        num,
                        folder,
                        exc,
                    )

        self.data_ready.emit(results)

    def _scan_large_gmail(self, acc: MailAccount) -> None:
        """Scan a Gmail API account for large Gmail and/or Drive items."""
        threshold_mb = self.params.get("threshold", 10)
        scan_mail = self.params.get("scan_mail", True)
        scan_drive = self.params.get("scan_drive", False)
        if not scan_mail and not scan_drive:
            self.log.emit("No Gmail or Drive source selected for scan.")
            self.data_ready.emit([])
            return

        results = []
        if scan_mail:
            self.log.emit(f"Scanning {acc.name} for emails > {threshold_mb}MB...")
            results.extend(self.service.scan_large_messages(threshold_mb))
        if scan_drive:
            self.log.emit(f"Scanning {acc.name} Drive for files > {threshold_mb}MB...")
            results.extend(self.service.scan_large_drive_files(threshold_mb))

        for item in results:
            item["account"] = acc.name
        self.data_ready.emit(results)

    def undo_delete(self, acc: MailAccount) -> None:
        """Moves previously trashed emails back to INBOX or out of Trash."""
        if getattr(acc, "protocol", "IMAP") == "Gmail API":
            self._undo_gmail_delete(acc)
            return

        items = self.params.get("items", [])
        my_items = [item for item in items if item["account"] == acc.name]
        if not my_items:
            return

        trash = self.service.find_trash_folder()
        self.log.emit(f"Restoring {len(my_items)} emails from trash in {acc.name}...")
        try:
            self.service.conn.select(trash)
            grouped_items = {}
            for item in my_items:
                grouped_items.setdefault(item.get("folder", "INBOX"), []).append(item)

            restored_total = 0
            for folder, folder_items in grouped_items.items():
                ids = [item["id"].encode() for item in folder_items]
                id_str = b",".join(ids).decode()
                copy_res = self.service.conn.copy(id_str, folder)
                if copy_res[0] == "OK":
                    self.service.conn.store(id_str, "+FLAGS", "\\Deleted")
                    self.service.conn.expunge()
                    restored_total += len(folder_items)
                    self.log.emit(f"   {len(folder_items)} email(s) restored to {folder}.")
                else:
                    self.log.emit(f"   Could not restore emails to {folder}: {copy_res}")
            if restored_total:
                self.log.emit(f"   Restored {restored_total} email(s).")
        except imaplib.IMAP4.error as exc:
            self.log.emit(f"   IMAP error during undo: {exc}")
        except Exception as exc:  # noqa: BLE001
            self.log.emit(f"   Unexpected error during undo: {exc}")

    def _undo_gmail_delete(self, acc: MailAccount) -> None:
        """Restore Gmail messages and Drive files from Trash."""
        items = self.params.get("items", [])
        my_items = [item for item in items if item["account"] == acc.name]
        if not my_items:
            return

        message_items = [
            item for item in my_items if item.get("item_type", "gmail_message") != "drive_file"
        ]
        drive_items = [
            item for item in my_items if item.get("item_type") == "drive_file"
        ]
        restored_messages = 0
        restored_drive_files = 0

        self.log.emit(f"Restoring {len(my_items)} item(s) from trash in {acc.name}...")
        for item in message_items:
            if self.service.restore_mail(item["id"]):
                restored_messages += 1
        for item in drive_items:
            if self.service.restore_drive_file(item["id"]):
                restored_drive_files += 1

        self.log.emit(
            f"   Restored {restored_messages} email(s) and {restored_drive_files} Drive file(s)."
        )

    def delete_items(self, acc: MailAccount) -> None:
        """Deletes selected emails from the 'Large Emails' tab."""
        if getattr(acc, "protocol", "IMAP") == "Gmail API":
            self._delete_gmail_items(acc)
            return

        items = self.params.get("items", [])
        my_items = [item for item in items if item["account"] == acc.name]
        if not my_items:
            return

        trash = self.service.find_trash_folder()
        grouped_items = {}
        for item in my_items:
            grouped_items.setdefault(item.get("folder", "INBOX"), []).append(item)

        total_ids = sum(len(group) for group in grouped_items.values())
        self.log.emit(f"Deleting {total_ids} emails in {acc.name}...")

        for folder, folder_items in grouped_items.items():
            self.service.conn.select(folder)
            ids = [item["id"].encode() for item in folder_items]
            id_str = b",".join(ids).decode()

            if self.safe_mode:
                if self.service.conn.copy(id_str, trash)[0] == "OK":
                    self.service.conn.store(id_str, "+FLAGS", "\\Deleted")
                    self.service.conn.expunge()
            else:
                self.service.conn.store(id_str, "+FLAGS", "\\Deleted")
                self.service.conn.expunge()

    def _delete_gmail_items(self, acc: MailAccount) -> None:
        """Delete or trash selected Gmail messages and Drive files."""
        items = self.params.get("items", [])
        my_items = [item for item in items if item["account"] == acc.name]
        if not my_items:
            return

        message_ids = [
            item["id"] for item in my_items if item.get("item_type", "gmail_message") != "drive_file"
        ]
        drive_ids = [
            item["id"] for item in my_items if item.get("item_type") == "drive_file"
        ]
        self.log.emit(f"Deleting {len(my_items)} item(s) in {acc.name}...")

        processed_messages = (
            self.service.trash_message_ids(message_ids)
            if self.safe_mode
            else self.service.delete_message_ids(message_ids)
        ) if message_ids else 0
        processed_drive_files = (
            self.service.trash_drive_file_ids(drive_ids)
            if self.safe_mode
            else self.service.delete_drive_file_ids(drive_ids)
        ) if drive_ids else 0

        self.log.emit(
            "   Processed "
            f"{processed_messages} email(s) and {processed_drive_files} Drive file(s)."
        )
