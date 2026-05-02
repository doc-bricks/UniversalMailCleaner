"""Gmail API service wrapper for UniversalMailCleaner.

Handles OAuth2 authentication and provides low-level Gmail/Drive API
operations: storage statistics, label listing, label-based deletion,
and trash restoration.
"""

import os
import logging
from pathlib import Path

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
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.auth.exceptions import RefreshError
    GOOGLE_AVAIL = True
except ImportError:
    GOOGLE_AVAIL = False


class GmailService:
    """Manages Gmail API authentication and low-level API operations.

    Wraps Gmail and Drive service objects. All log output goes to the
    module-level logger (no GUI dependency).
    """

    def __init__(
        self,
        token_path: Path = TOKEN_PATH,
        creds_path: Path = CREDS_PATH_LOCAL,
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
        if not GOOGLE_AVAIL:
            logger.error("Google libraries not available (pip install google-api-python-client google-auth-oauthlib)")
            return False

        # Ensure token directory exists
        self.token_path.parent.mkdir(parents=True, exist_ok=True)

        # Try loading existing token
        if self.token_path.exists():
            try:
                self.creds = Credentials.from_authorized_user_file(
                    str(self.token_path), SCOPES
                )
            except (ValueError, KeyError) as exc:
                logger.warning("Token file invalid, deleting: %s", exc)
                try:
                    os.remove(self.token_path)
                except OSError as exc2:
                    logger.warning("Could not delete token file: %s", exc2)
                self.creds = None

        # Refresh or re-authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    logger.info("Refreshing OAuth token...")
                    self.creds.refresh(Request())
                except RefreshError:
                    logger.warning("Token invalid, deleting and re-authenticating...")
                    try:
                        os.remove(self.token_path)
                    except OSError as exc:
                        logger.warning("Could not delete token file: %s", exc)
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
                    flow = InstalledAppFlow.from_client_secrets_file(
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
            self.gmail = build(
                "gmail", "v1", credentials=self.creds, cache_discovery=False
            )
            self.drive = build(
                "drive", "v3", credentials=self.creds, cache_discovery=False
            )
            logger.info("Google APIs connected.")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("API build error: %s", exc)
            return False

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

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

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
