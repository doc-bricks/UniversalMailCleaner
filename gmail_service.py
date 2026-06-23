"""Gmail API service wrapper for UniversalMailCleaner.

Handles OAuth2 authentication and provides low-level Gmail/Drive API
operations: storage statistics, label listing, label-based deletion,
and trash restoration.
"""

import json
import os
import math
import logging
from pathlib import Path
from typing import Callable, Optional

from models import CleanRule

logger = logging.getLogger(__name__)

# Token- und Credentials-Pfade
_LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home()))
TOKEN_PATH = _LOCALAPPDATA / "UniversalMailCleaner" / "gmail_token.json"

# credentials.json: zuerst neben dieser Datei, dann LOCALAPPDATA-Fallback
_HERE = Path(__file__).parent
CREDS_PATH_LOCAL = _HERE / "credentials.json"
CREDS_PATH_FALLBACK = _LOCALAPPDATA / "UniversalMailCleaner" / "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
]

GOOGLE_AVAIL = None
_GOOGLE_IMPORT_ERROR = None
_BUILD = None
_INSTALLED_APP_FLOW = None
_REQUEST = None
_CREDENTIALS = None
_REFRESH_ERROR = None


def _ensure_google_dependencies() -> bool:
    """Load Google client libraries only when OAuth is actually needed."""
    global GOOGLE_AVAIL
    global _GOOGLE_IMPORT_ERROR
    global _BUILD
    global _INSTALLED_APP_FLOW
    global _REQUEST
    global _CREDENTIALS
    global _REFRESH_ERROR

    if GOOGLE_AVAIL is True:
        return True
    if GOOGLE_AVAIL is False:
        return False

    try:
        from googleapiclient.discovery import build as build_fn
        from google_auth_oauthlib.flow import InstalledAppFlow as installed_app_flow_cls
        from google.auth.transport.requests import Request as request_cls
        from google.oauth2.credentials import Credentials as credentials_cls
        from google.auth.exceptions import RefreshError as refresh_error_cls
    except ImportError as exc:
        GOOGLE_AVAIL = False
        _GOOGLE_IMPORT_ERROR = exc
        return False

    _BUILD = build_fn
    _INSTALLED_APP_FLOW = installed_app_flow_cls
    _REQUEST = request_cls
    _CREDENTIALS = credentials_cls
    _REFRESH_ERROR = refresh_error_cls
    GOOGLE_AVAIL = True
    return True


class GmailService:
    """Manages Gmail API authentication and low-level API operations.

    Wraps Gmail and Drive service objects. All log output goes to the
    module-level logger (no GUI dependency).
    """

    def __init__(
        self,
        token_path: Path = TOKEN_PATH,
        creds_path: Path = CREDS_PATH_LOCAL,
        log_func: Optional[Callable[[str], None]] = None,
    ):
        """Initialise GmailService.

        Args:
            token_path:  Path where the OAuth token is stored/loaded.
            creds_path:  Path to credentials.json (OAuth client secrets).
                         Falls back to CREDS_PATH_FALLBACK if this path
                         does not exist.
        """
        self.token_path = Path(token_path)
        self.creds_path = Path(creds_path)
        self.gmail = None
        self.drive = None
        self.creds = None
        self.log = log_func or (lambda _msg: None)

    def _delete_token_file(self) -> None:
        """Delete the cached OAuth token if it exists."""
        try:
            os.remove(self.token_path)
        except OSError as exc:
            logger.warning("Could not delete token file: %s", exc)

    def _stored_token_has_required_scopes(self) -> bool:
        """Check whether the cached OAuth token already covers all scopes."""
        try:
            payload = json.loads(self.token_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("Token file invalid, deleting: %s", exc)
            return False

        token_scopes = payload.get("scopes") or payload.get("scope") or []
        if isinstance(token_scopes, str):
            token_scopes = token_scopes.split()

        missing_scopes = [scope for scope in SCOPES if scope not in token_scopes]
        if missing_scopes:
            logger.info(
                "Stored OAuth token missing required scopes: %s",
                ", ".join(missing_scopes),
            )
            return False

        return True

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def auth(self) -> bool:
        """Load/refresh token and build API service objects.

        Opens a browser window for OAuth2 consent on first run (or after
        token expiry/deletion).

        Returns:
            True if authentication succeeded, False otherwise.
        """
        if not _ensure_google_dependencies():
            logger.error("Google libraries not available (pip install google-api-python-client google-auth-oauthlib)")
            if _GOOGLE_IMPORT_ERROR is not None:
                logger.debug("Google import error: %s", _GOOGLE_IMPORT_ERROR)
            return False

        # Ensure token directory exists
        self.token_path.parent.mkdir(parents=True, exist_ok=True)

        # Try loading existing token
        if self.token_path.exists():
            if not self._stored_token_has_required_scopes():
                self._delete_token_file()
            else:
                try:
                    self.creds = _CREDENTIALS.from_authorized_user_file(
                        str(self.token_path), SCOPES
                    )
                except (ValueError, KeyError) as exc:
                    logger.warning("Token file invalid, deleting: %s", exc)
                    self._delete_token_file()
                    self.creds = None

        # Refresh or re-authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    logger.info("Refreshing OAuth token...")
                    self.creds.refresh(_REQUEST())
                    try:
                        with open(self.token_path, "w", encoding="utf-8") as fh:
                            fh.write(self.creds.to_json())
                    except OSError as exc:
                        logger.warning("Could not save refreshed token: %s", exc)
                except _REFRESH_ERROR:
                    logger.warning("Token invalid, deleting and re-authenticating...")
                    self._delete_token_file()
                    self.creds = None
                except Exception as exc:  # noqa: BLE001
                    logger.error("Auth error during refresh: %s", exc)
                    self.creds = None

            if not self.creds:
                cred_path = (
                    self.creds_path
                    if self.creds_path.exists()
                    else CREDS_PATH_FALLBACK
                )
                if not cred_path.exists():
                    logger.error(
                        "No credentials.json found at '%s' or '%s'",
                        self.creds_path,
                        CREDS_PATH_FALLBACK,
                    )
                    return False

                logger.info("Opening browser for OAuth2 login...")
                try:
                    flow = _INSTALLED_APP_FLOW.from_client_secrets_file(
                        str(cred_path), SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                    with open(self.token_path, "w", encoding="utf-8") as fh:
                        fh.write(self.creds.to_json())
                    logger.info("Token saved to '%s'", self.token_path)
                except Exception as exc:  # noqa: BLE001
                    logger.error("OAuth login failed: %s", exc)
                    return False

        # Build API clients
        try:
            self.gmail = _BUILD(
                "gmail", "v1", credentials=self.creds, cache_discovery=False
            )
            self.drive = _BUILD(
                "drive", "v3", credentials=self.creds, cache_discovery=False
            )
            logger.info("Google APIs connected.")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("API build error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Search helpers
    # ------------------------------------------------------------------

    def build_search_query(self, rule: CleanRule) -> Optional[str]:
        """Translate a CleanRule into a Gmail API query string."""
        try:
            if rule.filter_type == "older_than_days":
                days = int(rule.value)
                if days <= 0:
                    return None
                return f"older_than:{days}d -label:TRASH"

            if rule.filter_type == "sender":
                safe_value = rule.value.replace('"', "").strip()
                if not safe_value:
                    return None
                return f'from:"{safe_value}" -label:TRASH'

            if rule.filter_type == "subject":
                safe_value = rule.value.replace('"', "").strip()
                if not safe_value:
                    return None
                return f'subject:"{safe_value}" -label:TRASH'

            if rule.filter_type == "size_mb":
                size_mb = float(rule.value)
                if size_mb <= 0:
                    return None
                size_limit = max(1, math.ceil(size_mb))
                return f"larger:{size_limit}M -label:TRASH"
        except (TypeError, ValueError) as exc:
            logger.warning("build_search_query error for rule '%s': %s", rule.name, exc)
            return None

        return None

    def list_message_ids(self, query: str, max_results: Optional[int] = None) -> list[str]:
        """Return Gmail message IDs matching a query."""
        if not self.gmail:
            logger.warning("list_message_ids called before successful auth()")
            return []

        ids: list[str] = []
        page_token = None

        while True:
            try:
                kwargs = {
                    "userId": "me",
                    "q": query,
                    "maxResults": 100,
                }
                if page_token:
                    kwargs["pageToken"] = page_token
                if max_results is not None:
                    remaining = max_results - len(ids)
                    if remaining <= 0:
                        break
                    kwargs["maxResults"] = min(kwargs["maxResults"], remaining)

                response = self.gmail.users().messages().list(**kwargs).execute()
                ids.extend(msg["id"] for msg in response.get("messages", []))

                page_token = response.get("nextPageToken")
                if not page_token:
                    break
            except Exception as exc:  # noqa: BLE001
                logger.error("Gmail query failed for '%s': %s", query, exc)
                break

        return ids

    @staticmethod
    def _extract_header(headers: list, name: str, default: str = "") -> str:
        """Read a single header value from a Gmail message payload."""
        target = name.lower()
        for header in headers or []:
            if header.get("name", "").lower() == target:
                return header.get("value", default)
        return default

    def scan_large_messages(self, threshold_mb: int, max_results: int = 50) -> list[dict]:
        """Return metadata for large Gmail messages above a threshold."""
        if not self.gmail:
            logger.warning("scan_large_messages called before successful auth()")
            return []

        query = f"larger:{max(1, int(threshold_mb))}M -label:TRASH"
        results = []

        for msg_id in self.list_message_ids(query, max_results=max_results):
            try:
                full = self.gmail.users().messages().get(userId="me", id=msg_id).execute()
                payload = full.get("payload", {})
                headers = payload.get("headers", [])
                subject = self._extract_header(headers, "Subject", "(Kein Betreff)")
                date_str = self._extract_header(headers, "Date", "")[:16]
                size = int(full.get("sizeEstimate", 0)) / (1024 * 1024)
                results.append({
                    "id": msg_id,
                    "folder": "Gmail",
                    "subject": subject,
                    "size": size,
                    "date": date_str,
                    "item_type": "gmail_message",
                })
            except Exception as exc:  # noqa: BLE001
                logger.warning("Large-message metadata skipped for %s: %s", msg_id, exc)

        return results

    def scan_large_drive_files(
        self,
        threshold_mb: int,
        max_results: int = 50,
    ) -> list[dict]:
        """Return metadata for large Drive files above a threshold."""
        if not self.drive:
            logger.warning("scan_large_drive_files called before successful auth()")
            return []

        min_size_bytes = int(threshold_mb) * 1024 * 1024
        query = (
            "trashed = false "
            "and mimeType != 'application/vnd.google-apps.folder'"
        )
        fields = "nextPageToken, files(id, name, size, modifiedTime, webViewLink)"
        request_kwargs = {
            "q": query,
            "fields": fields,
            "pageSize": min(100, max(1, int(max_results))),
        }

        results = []
        page_token = None

        while len(results) < max_results:
            if page_token:
                request_kwargs["pageToken"] = page_token
            else:
                request_kwargs.pop("pageToken", None)

            try:
                response = self.drive.files().list(
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    corpora="allDrives",
                    **request_kwargs,
                ).execute()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "All-drives Drive scan failed, falling back to personal drive: %s",
                    exc,
                )
                try:
                    response = self.drive.files().list(
                        spaces="drive",
                        **request_kwargs,
                    ).execute()
                except Exception as exc2:  # noqa: BLE001
                    logger.error("Drive scan failed: %s", exc2)
                    return results

            for drive_file in response.get("files", []):
                try:
                    size_bytes = int(drive_file.get("size", 0))
                    if size_bytes <= min_size_bytes:
                        continue
                    results.append(
                        {
                            "id": drive_file["id"],
                            "folder": "Drive",
                            "subject": drive_file.get("name", "(Ohne Name)"),
                            "size": size_bytes / (1024 * 1024),
                            "date": drive_file.get("modifiedTime", "")[:16],
                            "item_type": "drive_file",
                            "link": drive_file.get("webViewLink", ""),
                        }
                    )
                    if len(results) >= max_results:
                        break
                except (KeyError, TypeError, ValueError) as exc:
                    logger.warning("Large-drive-file metadata skipped: %s", exc)

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return results

    # ------------------------------------------------------------------
    # Storage statistics
    # ------------------------------------------------------------------

    def get_storage_stats(self) -> dict:
        """Fetch Gmail message count and Drive quota statistics.

        Returns:
            Dict with keys:
                gmail_used  (int)  -- total number of messages
                drive_total (int)  -- Drive quota in bytes
                drive_used  (int)  -- Drive usage in bytes
                drive_trash (int)  -- Trash usage in bytes
        """
        stats = {
            "gmail_used": 0,
            "drive_total": 0,
            "drive_used": 0,
            "drive_trash": 0,
        }
        if not self.gmail or not self.drive:
            logger.warning("get_storage_stats called before successful auth()")
            return stats

        try:
            profile = self.gmail.users().getProfile(userId="me").execute()
            stats["gmail_used"] = int(profile.get("messagesTotal", 0))
        except Exception as exc:  # noqa: BLE001
            logger.error("Gmail profile error: %s", exc)

        try:
            about = self.drive.about().get(fields="storageQuota").execute()
            quota = about.get("storageQuota", {})
            stats["drive_total"] = int(quota.get("limit", 0))
            stats["drive_used"] = int(quota.get("usage", 0))
            stats["drive_trash"] = int(quota.get("usageInDriveTrash", 0))
        except Exception as exc:  # noqa: BLE001
            logger.error("Drive quota error: %s", exc)

        return stats

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_labels(self) -> list:
        """Fetch all Gmail labels.

        Returns:
            List of dicts, each with at least ``id``, ``name``, and
            ``type`` (``"system"`` or ``"user"``).
        """
        if not self.gmail:
            logger.warning("get_labels called before successful auth()")
            return []
        try:
            result = self.gmail.users().labels().list(userId="me").execute()
            return result.get("labels", [])
        except Exception as exc:  # noqa: BLE001
            logger.error("Label fetch error: %s", exc)
            return []

    def create_label(self, name: str) -> dict:
        """Create a new user label.

        Args:
            name: Display name for the new label.

        Returns:
            The created label payload returned by the Gmail API.
        """
        if not self.gmail:
            logger.warning("create_label called before successful auth()")
            return {}

        label_name = name.strip()
        if not label_name:
            raise ValueError("Label name must not be empty.")

        body = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        result = self.gmail.users().labels().create(userId="me", body=body).execute()
        logger.info("Created Gmail label '%s'.", label_name)
        return result or {}

    def rename_label(self, label_id: str, new_name: str) -> dict:
        """Rename an existing user label.

        Args:
            label_id: Gmail label ID (for example ``"Label_123"``).
            new_name: New display name for the label.

        Returns:
            The updated label payload returned by the Gmail API.
        """
        if not self.gmail:
            logger.warning("rename_label called before successful auth()")
            return {}

        label_name = new_name.strip()
        if not label_name:
            raise ValueError("New label name must not be empty.")

        result = self.gmail.users().labels().patch(
            userId="me",
            id=label_id,
            body={"name": label_name},
        ).execute()
        logger.info("Renamed Gmail label '%s' to '%s'.", label_id, label_name)
        return result or {}

    def delete_label(self, label_id: str) -> bool:
        """Delete an existing user label definition.

        Args:
            label_id: Gmail label ID (for example ``"Label_123"``).

        Returns:
            True on success, False if the service is not authenticated.
        """
        if not self.gmail:
            logger.warning("delete_label called before successful auth()")
            return False

        self.gmail.users().labels().delete(userId="me", id=label_id).execute()
        logger.info("Deleted Gmail label '%s'.", label_id)
        return True

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def trash_message_ids(self, message_ids: list[str]) -> int:
        """Move a list of Gmail messages to Trash."""
        if not self.gmail:
            logger.warning("trash_message_ids called before successful auth()")
            return 0

        processed = 0
        for msg_id in message_ids:
            try:
                self.gmail.users().messages().trash(userId="me", id=msg_id).execute()
                processed += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Could not trash message %s: %s", msg_id, exc)
        return processed

    def delete_message_ids(self, message_ids: list[str]) -> int:
        """Permanently delete a list of Gmail messages."""
        if not self.gmail:
            logger.warning("delete_message_ids called before successful auth()")
            return 0

        # FIX: messages().delete() braucht den Scope 'https://mail.google.com/', der in
        # SCOPES fehlt (nur gmail.modify) -> jeder Aufruf 403, per-Message geschluckt,
        # Rueckgabe processed=0 (STILLER Fehlschlag, GUI meldet faelschlich Erfolg/0).
        # Konsistent zu delete_by_label hart abweisen statt Loeschen vorzutaeuschen.
        raise PermissionError(
            "Permanent deletion requires the 'https://mail.google.com/' scope "
            "which is not included. Use trashing (move to Trash) instead."
        )

        processed = 0
        for msg_id in message_ids:
            try:
                self.gmail.users().messages().delete(userId="me", id=msg_id).execute()
                processed += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Could not delete message %s: %s", msg_id, exc)
        return processed

    def trash_drive_file_ids(self, file_ids: list[str]) -> int:
        """Move a list of Drive files to Trash."""
        if not self.drive:
            logger.warning("trash_drive_file_ids called before successful auth()")
            return 0

        processed = 0
        for file_id in file_ids:
            try:
                self.drive.files().update(
                    fileId=file_id,
                    body={"trashed": True},
                    supportsAllDrives=True,
                ).execute()
                processed += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Could not trash Drive file %s: %s", file_id, exc)
        return processed

    def delete_drive_file_ids(self, file_ids: list[str]) -> int:
        """Permanently delete a list of Drive files."""
        if not self.drive:
            logger.warning("delete_drive_file_ids called before successful auth()")
            return 0

        processed = 0
        for file_id in file_ids:
            try:
                self.drive.files().delete(
                    fileId=file_id,
                    supportsAllDrives=True,
                ).execute()
                processed += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Could not delete Drive file %s: %s", file_id, exc)
        return processed

    def process_rule(self, rule: CleanRule, trash: bool = True) -> int:
        """Execute one CleanRule via the Gmail API backend."""
        query = self.build_search_query(rule)
        if not query:
            logger.warning("Unsupported Gmail rule skipped: %s", rule.name)
            return 0

        message_ids = self.list_message_ids(query)
        if not message_ids:
            self.log("   No matches.")
            return 0

        self.log(f"   Found {len(message_ids)} emails. Processing...")
        processed = (
            self.trash_message_ids(message_ids)
            if trash
            else self.delete_message_ids(message_ids)
        )
        return processed

    def delete_by_label(self, label_id: str, trash: bool = True) -> int:
        """Move or delete all messages with the given label.

        Note: ``trash=False`` requires the ``https://mail.google.com/``
        scope which is NOT included in the default SCOPES. Passing
        ``trash=False`` will raise ``PermissionError`` to avoid a
        misleading 403 from the API.

        Args:
            label_id:  Gmail label ID (e.g. ``"Label_123"``).
            trash:     If True, move to Trash; if False, permanently
                       delete (requires extra scope -- raises PermissionError).

        Returns:
            Number of messages successfully processed.
        """
        if not self.gmail:
            logger.warning("delete_by_label called before successful auth()")
            return 0

        if not trash:
            raise PermissionError(
                "Permanent deletion requires the 'https://mail.google.com/' scope "
                "which is not included. Use trash=True instead."
            )

        processed = 0
        page_token = None

        while True:
            try:
                kwargs = {
                    "userId": "me",
                    "labelIds": [label_id],
                    "maxResults": 500,
                }
                if page_token:
                    kwargs["pageToken"] = page_token

                response = self.gmail.users().messages().list(**kwargs).execute()
                messages = response.get("messages", [])

                for msg in messages:
                    try:
                        self.gmail.users().messages().trash(
                            userId="me", id=msg["id"]
                        ).execute()
                        processed += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Could not trash message %s: %s", msg["id"], exc)

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            except Exception as exc:  # noqa: BLE001
                logger.error("delete_by_label error: %s", exc)
                break

        logger.info("delete_by_label('%s'): %d messages processed.", label_id, processed)
        return processed

    # ------------------------------------------------------------------
    # Restore
    # ------------------------------------------------------------------

    def restore_mail(self, msg_id: str) -> bool:
        """Restore a message from Trash back to Inbox.

        Args:
            msg_id: Gmail message ID.

        Returns:
            True on success, False otherwise.
        """
        if not self.gmail:
            logger.warning("restore_mail called before successful auth()")
            return False
        try:
            self.gmail.users().messages().untrash(
                userId="me", id=msg_id
            ).execute()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Restore mail failed for %s: %s", msg_id, exc)
            return False

    def restore_drive_file(self, file_id: str) -> bool:
        """Restore a Drive file from Trash."""
        if not self.drive:
            logger.warning("restore_drive_file called before successful auth()")
            return False
        try:
            self.drive.files().update(
                fileId=file_id,
                body={"trashed": False},
                supportsAllDrives=True,
            ).execute()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Restore Drive file failed for %s: %s", file_id, exc)
            return False
