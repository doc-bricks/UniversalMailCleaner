"""IMAP client logic for Universal Mail Cleaner.

Contains ImapService (IMAP connection/operations) and decode_header_str helper.
"""
import imaplib
import email
import email.header
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

from models import MailAccount, CleanRule

try:
    import keyring
    KEYRING_AVAIL = True
except ImportError:
    KEYRING_AVAIL = False

APP_NAME = "MailCleaner_V8_Universal"
logger = logging.getLogger(APP_NAME)


def decode_header_str(header_val) -> str:
    """Decodes an email header value, handling various encodings.

    Args:
        header_val: Raw header value (str or bytes).

    Returns:
        Decoded header string, or a fallback string on error.
    """
    if not header_val:
        return "(No Subject)"
    try:
        decoded_list = email.header.decode_header(header_val)
        val = ""
        for text, encoding in decoded_list:
            if isinstance(text, bytes):
                if encoding:
                    val += text.decode(encoding, errors='ignore')
                else:
                    val += text.decode('utf-8', errors='ignore')
            else:
                val += str(text)
        return val
    except (UnicodeDecodeError, LookupError, AttributeError) as e:
        logger.debug(f"Header decoding error: {e}")
        return str(header_val) if header_val else "(Decoding error)"


class ImapService:
    """IMAP service for email operations.

    Manages IMAP4_SSL connections to email accounts and provides
    functions for searching, deleting, and trash management.
    """

    def __init__(self, log_func: Callable[[str], None]) -> None:
        """Initializes the IMAP service.

        Args:
            log_func: Callback function for log output (e.g. Signal.emit).
        """
        self.log = log_func
        self.conn = None
        self.current_account = None

    def connect(self, account: MailAccount) -> bool:
        """Establishes an IMAP4_SSL connection to an account.

        Args:
            account: MailAccount object with host, port, and user.

        Returns:
            True on successful connection, False on error.
        """
        self.current_account = account
        pwd = ""
        if KEYRING_AVAIL:
            try:
                pwd = keyring.get_password(APP_NAME, account.name)
            except Exception as e:
                logger.warning(f"Keyring read error for {account.name}: {e}")

        if not pwd:
            self.log(f"❌ No password found for {account.name}.")
            return False

        try:
            self.log(f"🔌 Connecting to {account.host}...")
            self.conn = imaplib.IMAP4_SSL(account.host, account.port)
            self.conn.login(account.user, pwd)
            self.log(f"✅ Logged in as {account.user}")
            return True
        except Exception as e:
            self.log(f"❌ Login error ({account.name}): {e}")
            return False

    def disconnect(self) -> None:
        """Closes the IMAP connection cleanly."""
        if self.conn:
            try:
                self.conn.logout()
            except Exception as e:
                logger.warning(f"IMAP logout error: {e}")
            self.conn = None

    def find_trash_folder(self) -> str:
        """Tries to detect the trash folder.

        Returns:
            Name of the trash folder (fallback: "Trash").
        """
        if self.current_account.trash_folder:
            return self.current_account.trash_folder

        candidates = ["Trash", "Papierkorb", "Deleted Items",
                      "Gelöschte Elemente", "INBOX.Trash", "Bin"]
        try:
            status, folders = self.conn.list()
            if status != 'OK':
                return "Trash"

            folder_names = []
            for f in folders:
                name = f.decode().split(' "')[-1].replace('"', '').strip()
                folder_names.append(name)

            for c in candidates:
                for f in folder_names:
                    if c.lower() == f.lower() or f.endswith(f"/{c}"):
                        self.log(f"🗑️ Trash folder detected: {f}")
                        return f

            return "Trash"
        except Exception as e:
            logger.warning(f"find_trash_folder error: {e}")
            return "Trash"

    def list_folders(self) -> list:
        """Lists all available IMAP folders for the connected account.

        Returns:
            List of folder name strings, or ['INBOX'] on error.
        """
        if not self.conn:
            return ["INBOX"]
        try:
            status, raw_folders = self.conn.list()
            if status != "OK":
                return ["INBOX"]
            folders = []
            for entry in raw_folders:
                if not entry:
                    continue
                decoded = entry.decode("utf-8", errors="replace") if isinstance(entry, bytes) else entry
                # Format: (\HasNoChildren) "/" "INBOX"  or  (\HasNoChildren) "/" INBOX
                parts = decoded.rsplit(" ", 1)
                name = parts[-1].strip().strip('"')
                if name:
                    folders.append(name)
            return folders if folders else ["INBOX"]
        except Exception as e:
            logger.warning(f"list_folders error: {e}")
            return ["INBOX"]

    def get_search_criteria(self, rule: CleanRule) -> Optional[str]:
        """Translates a CleanRule into an IMAP search command string.

        Args:
            rule: CleanRule object with filter_type and value.

        Returns:
            IMAP search string or None on error.
        """
        try:
            if rule.filter_type == "older_than_days":
                days = int(rule.value)
                cutoff = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
                return f'(BEFORE "{cutoff}")'
            elif rule.filter_type == "sender":
                safe_value = rule.value.replace('\\', '\\\\').replace('"', '')
                return f'(FROM "{safe_value}")'
            elif rule.filter_type == "subject":
                safe_value = rule.value.replace('\\', '\\\\').replace('"', '')
                return f'(SUBJECT "{safe_value}")'
            elif rule.filter_type == "size_mb":
                bytes_val = int(float(rule.value) * 1024 * 1024)
                return f'(LARGER {bytes_val})'
        except Exception as e:
            logger.warning(f"get_search_criteria error for rule '{rule.name}': {e}")
        return None
