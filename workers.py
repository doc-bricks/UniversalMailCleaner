"""Background worker thread for Universal Mail Cleaner.

Contains the Worker QThread class for IMAP operations.
"""
import email
import logging
import imaplib
from typing import List

from PySide6.QtCore import QThread, Signal

from models import MailAccount
from imap_client import ImapService, decode_header_str

APP_NAME = "MailCleaner_V8_Universal"
logger = logging.getLogger(APP_NAME)


class Worker(QThread):
    """Background worker for IMAP operations (QThread).

    Executes time-intensive IMAP tasks (rules, scanning, deleting) in a
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
            mode: "rules", "scan_large", or "delete".
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
        """Main loop of the worker (called automatically by QThread).

        Connects to the relevant accounts and executes the selected mode.
        """
        self.service = ImapService(self.log.emit)

        target_acc_name = self.params.get("target_account", "Alle")
        to_process = (self.accounts if target_acc_name == "Alle"
                      else [a for a in self.accounts if a.name == target_acc_name])

        if not to_process:
            self.log.emit("❌ No account selected.")
            self.finished.emit("Aborted.")
            return

        for acc in to_process:
            if self.isInterruptionRequested():
                break
            if not self.service.connect(acc):
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
            except Exception as e:
                self.log.emit(f"❌ Runtime error for {acc.name}: {e}")
            finally:
                self.service.disconnect()

        self.finished.emit("Operation completed.")

    def run_rules(self, acc: MailAccount) -> None:
        """Executes automatic cleanup rules on an account.

        Iterates over all selected folders (params key "folders", default ["INBOX"]).

        Args:
            acc: Account to process.
        """
        rules = self.params.get("rules", [])
        trash_folder = self.service.find_trash_folder()
        folders = self.params.get("folders", ["INBOX"])

        for folder in folders:
            if self.isInterruptionRequested():
                break
            try:
                self.service.conn.select(folder)
                self.log.emit(f"📂 Folder: {folder}")
            except Exception as e:
                self.log.emit(f"⚠️ Cannot select folder '{folder}': {e}")
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

                self.log.emit(f"⚙️ Rule '{rule.name}' on {acc.name}/{folder}...")
                typ, data = self.service.conn.search(None, criteria)

                if typ == 'OK':
                    ids = data[0].split()
                    if not ids:
                        self.log.emit("   No matches.")
                        continue

                    self.log.emit(f"   Found {len(ids)} emails. Processing...")
                    id_str = b','.join(ids).decode()

                    try:
                        if self.safe_mode:
                            copy_result = self.service.conn.copy(id_str, trash_folder)
                            if copy_result[0] == 'OK':
                                self.service.conn.store(id_str, '+FLAGS', '\\Deleted')
                                self.service.conn.expunge()
                                self.log.emit("   ✅ Moved to trash.")
                            else:
                                self.log.emit(f"   ⚠️ Could not move to trash: {copy_result}")
                        else:
                            self.service.conn.store(id_str, '+FLAGS', '\\Deleted')
                            self.service.conn.expunge()
                            self.log.emit("   🗑️ Permanently deleted.")
                    except imaplib.IMAP4.error as e:
                        self.log.emit(f"   ❌ IMAP error during deletion: {e}")
                    except Exception as e:
                        self.log.emit(f"   ❌ Unexpected error: {e}")

    def scan_large(self, acc: MailAccount) -> None:
        """Scans an account for large emails across multiple folders.

        Args:
            acc: Account to scan.
        """
        threshold_mb = self.params.get("threshold", 10)
        limit_bytes = int(threshold_mb * 1024 * 1024)
        folders = self.params.get("folders", ["INBOX"])

        self.log.emit(f"🔍 Scanning {acc.name} for emails > {threshold_mb}MB...")
        results = []

        for folder in folders:
            if self.isInterruptionRequested():
                break
            try:
                self.service.conn.select(folder, readonly=True)
            except Exception as e:
                self.log.emit(f"⚠️ Cannot select folder '{folder}': {e}")
                continue

            typ, data = self.service.conn.search(None, f'(LARGER {limit_bytes})')
            if typ != 'OK':
                continue

            ids = data[0].split()
            ids = ids[-50:]

            for num in ids:
                if self.isInterruptionRequested():
                    break
                try:
                    res, fetch_data = self.service.conn.fetch(
                        num, '(RFC822.SIZE BODY.PEEK[HEADER.FIELDS (SUBJECT DATE)])'
                    )

                    size_bytes = 0
                    subject = "Unknown"
                    date_str = ""

                    for response_part in fetch_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = decode_header_str(msg["Subject"])
                            date_str = msg["Date"][:16]

                            meta = response_part[0].decode()
                            if "RFC822.SIZE" in meta:
                                parts = meta.split("RFC822.SIZE")
                                if len(parts) > 1:
                                    size_bytes = int(
                                        parts[1].strip().split()[0].replace(')', '')
                                    )

                    if size_bytes > 0:
                        results.append({
                            "account": acc.name,
                            "folder": folder,
                            "id": num.decode(),
                            "subject": subject,
                            "size": size_bytes / (1024 * 1024),
                            "date": date_str
                        })

                except Exception as e:
                    logger.warning(f"scan_large: error fetching email {num} in {folder}: {e}")

        self.data_ready.emit(results)

    def undo_delete(self, acc: MailAccount) -> None:
        """Moves previously trashed emails back to INBOX (undo last delete).

        Expects params["items"] as a list of email dicts with 'account', 'folder', 'id'.
        Searches the trash folder for matching message IDs and moves them to INBOX.

        Args:
            acc: Account to process.
        """
        items = self.params.get("items", [])
        my_items = [i for i in items if i['account'] == acc.name]
        if not my_items:
            return

        trash = self.service.find_trash_folder()
        self.log.emit(f"↩️ Restoring {len(my_items)} emails from trash in {acc.name}...")
        try:
            self.service.conn.select(trash)
            ids = [i['id'].encode() for i in my_items]
            id_str = b','.join(ids).decode()
            copy_res = self.service.conn.copy(id_str, "INBOX")
            if copy_res[0] == 'OK':
                self.service.conn.store(id_str, '+FLAGS', '\\Deleted')
                self.service.conn.expunge()
                self.log.emit(f"   ✅ {len(my_items)} email(s) restored to INBOX.")
            else:
                self.log.emit(f"   ⚠️ Could not restore emails: {copy_res}")
        except imaplib.IMAP4.error as e:
            self.log.emit(f"   ❌ IMAP error during undo: {e}")
        except Exception as e:
            self.log.emit(f"   ❌ Unexpected error during undo: {e}")

    def delete_items(self, acc: MailAccount) -> None:
        """Deletes selected emails from the 'Large Emails' tab.

        Args:
            acc: Account to process.
        """
        items = self.params.get("items", [])
        my_items = [i for i in items if i['account'] == acc.name]

        if not my_items:
            return

        trash = self.service.find_trash_folder()
        self.service.conn.select("INBOX")

        ids = [i['id'].encode() for i in my_items]
        id_str = b','.join(ids).decode()

        self.log.emit(f"🗑️ Deleting {len(ids)} emails in {acc.name}...")

        if self.safe_mode:
            if self.service.conn.copy(id_str, trash)[0] == 'OK':
                self.service.conn.store(id_str, '+FLAGS', '\\Deleted')
                self.service.conn.expunge()
        else:
            self.service.conn.store(id_str, '+FLAGS', '\\Deleted')
            self.service.conn.expunge()
