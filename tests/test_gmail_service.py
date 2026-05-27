"""Unit tests for GmailService."""

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gmail_service import GmailService
from models import CleanRule


class _Executable:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _FakeMessagesApi:
    def __init__(self, list_responses=None, get_responses=None):
        self.list_responses = list(list_responses or [])
        self.get_responses = dict(get_responses or {})
        self.list_calls = []
        self.get_calls = []
        self.trash_calls = []
        self.delete_calls = []

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        response = self.list_responses.pop(0) if self.list_responses else {}
        return _Executable(response)

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return _Executable(self.get_responses[kwargs["id"]])

    def trash(self, **kwargs):
        self.trash_calls.append(kwargs)
        return _Executable({})

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)
        return _Executable({})


class _FakeLabelsApi:
    def __init__(self, labels=None):
        self.labels = list(labels or [])
        self.create_calls = []
        self.patch_calls = []
        self.delete_calls = []

    def list(self, **kwargs):
        return _Executable({"labels": self.labels})

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        body = dict(kwargs.get("body", {}))
        label = {
            "id": body.get("id", f"Label_{len(self.labels) + 1}"),
            "name": body.get("name", ""),
            "type": body.get("type", "user"),
            "labelListVisibility": body.get("labelListVisibility"),
            "messageListVisibility": body.get("messageListVisibility"),
        }
        self.labels.append(label)
        return _Executable(label)

    def patch(self, **kwargs):
        self.patch_calls.append(kwargs)
        label_id = kwargs["id"]
        body = dict(kwargs.get("body", {}))
        for label in self.labels:
            if label.get("id") == label_id:
                label.update(body)
                return _Executable(label)
        label = {"id": label_id, **body}
        self.labels.append(label)
        return _Executable(label)

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)
        label_id = kwargs["id"]
        self.labels = [label for label in self.labels if label.get("id") != label_id]
        return _Executable({})


class _FakeProfileApi:
    def __init__(self, profile):
        self.profile = profile

    def execute(self):
        return self.profile


class _FakeUsersApi:
    def __init__(self, messages_api, labels=None, profile=None):
        self._messages_api = messages_api
        self._labels_api = _FakeLabelsApi(labels)
        self._profile = profile or {"messagesTotal": 0}

    def messages(self):
        return self._messages_api

    def labels(self):
        return self._labels_api

    def getProfile(self, **kwargs):
        return _FakeProfileApi(self._profile)


class _FakeGmailApi:
    def __init__(self, messages_api, labels=None, profile=None):
        self._users_api = _FakeUsersApi(messages_api, labels=labels, profile=profile)

    def users(self):
        return self._users_api


class _FakeDriveAboutApi:
    def __init__(self, quota):
        self.quota = quota

    def get(self, **kwargs):
        return _Executable({"storageQuota": self.quota})


class _FakeDriveFilesApi:
    def __init__(self, list_responses=None):
        self.list_responses = list(list_responses or [])
        self.list_calls = []
        self.update_calls = []
        self.delete_calls = []

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        response = self.list_responses.pop(0) if self.list_responses else {}
        return _Executable(response)

    def update(self, **kwargs):
        self.update_calls.append(kwargs)
        return _Executable({})

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)
        return _Executable({})


class _FakeDriveApi:
    def __init__(self, quota, list_responses=None):
        self._about_api = _FakeDriveAboutApi(quota)
        self._files_api = _FakeDriveFilesApi(list_responses=list_responses)

    def about(self):
        return self._about_api

    def files(self):
        return self._files_api


class TestGmailService(unittest.TestCase):
    def setUp(self):
        self.service = GmailService()

    def test_module_import_stays_lazy_without_google_clients(self):
        project_root = Path(__file__).resolve().parent.parent
        script = (
            "import sys; "
            "import gmail_service; "
            "loaded = [name for name in ("
            "'googleapiclient.discovery', "
            "'google_auth_oauthlib.flow', "
            "'google.auth.transport.requests', "
            "'google.oauth2.credentials'"
            ") if name in sys.modules]; "
            "print('loaded=' + ','.join(loaded))"
        )
        result = subprocess.run(
            [sys.executable, "-u", "-c", script],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "loaded=")

    def test_build_search_query_maps_supported_rule_types(self):
        older = CleanRule("Old", "Alle", "older_than_days", "30")
        sender = CleanRule("Sender", "Alle", "sender", 'spam"@example.com')
        subject = CleanRule("Subject", "Alle", "subject", 'Sale "Now"')
        size = CleanRule("Large", "Alle", "size_mb", "5.5")

        self.assertEqual(
            self.service.build_search_query(older),
            "older_than:30d -label:TRASH",
        )
        self.assertEqual(
            self.service.build_search_query(sender),
            'from:"spam@example.com" -label:TRASH',
        )
        self.assertEqual(
            self.service.build_search_query(subject),
            'subject:"Sale Now" -label:TRASH',
        )
        self.assertEqual(
            self.service.build_search_query(size),
            "larger:6M -label:TRASH",
        )

    def test_build_search_query_rejects_invalid_values(self):
        invalid = CleanRule("Broken", "Alle", "older_than_days", "abc")
        self.assertIsNone(self.service.build_search_query(invalid))

    def test_get_storage_stats_reads_gmail_and_drive_values(self):
        messages_api = _FakeMessagesApi()
        self.service.gmail = _FakeGmailApi(
            messages_api,
            profile={"messagesTotal": 42},
        )
        self.service.drive = _FakeDriveApi(
            {"limit": "1000", "usage": "250", "usageInDriveTrash": "25"}
        )

        stats = self.service.get_storage_stats()

        self.assertEqual(stats["gmail_used"], 42)
        self.assertEqual(stats["drive_total"], 1000)
        self.assertEqual(stats["drive_used"], 250)
        self.assertEqual(stats["drive_trash"], 25)

    def test_scan_large_messages_reads_message_metadata(self):
        messages_api = _FakeMessagesApi(
            list_responses=[{"messages": [{"id": "m1"}, {"id": "m2"}]}],
            get_responses={
                "m1": {
                    "sizeEstimate": 12 * 1024 * 1024,
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Invoice"},
                            {"name": "Date", "value": "2026-05-09 08:00:00"},
                        ]
                    },
                },
                "m2": {
                    "sizeEstimate": 3 * 1024 * 1024,
                    "payload": {"headers": []},
                },
            },
        )
        self.service.gmail = _FakeGmailApi(messages_api)

        results = self.service.scan_large_messages(10)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "m1")
        self.assertEqual(results[0]["item_type"], "gmail_message")
        self.assertEqual(results[0]["subject"], "Invoice")
        self.assertEqual(results[0]["folder"], "Gmail")
        self.assertEqual(results[1]["subject"], "(Kein Betreff)")
        self.assertEqual(messages_api.list_calls[0]["q"], "larger:10M -label:TRASH")

    def test_scan_large_drive_files_reads_drive_metadata(self):
        self.service.drive = _FakeDriveApi(
            {},
            list_responses=[
                {
                    "files": [
                        {
                            "id": "drive-small",
                            "name": "Small.txt",
                            "size": str(2 * 1024 * 1024),
                            "modifiedTime": "2026-05-19T08:10:00Z",
                        },
                        {
                            "id": "drive-1",
                            "name": "Archive.zip",
                            "size": str(15 * 1024 * 1024),
                            "modifiedTime": "2026-05-19T08:15:00Z",
                            "webViewLink": "https://drive.example/file/drive-1",
                        }
                    ]
                }
            ],
        )

        results = self.service.scan_large_drive_files(10)
        files_api = self.service.drive.files()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "drive-1")
        self.assertEqual(results[0]["item_type"], "drive_file")
        self.assertEqual(results[0]["subject"], "Archive.zip")
        self.assertEqual(results[0]["folder"], "Drive")
        self.assertEqual(files_api.list_calls[0]["corpora"], "allDrives")
        self.assertTrue(files_api.list_calls[0]["supportsAllDrives"])
        self.assertNotIn("size >", files_api.list_calls[0]["q"])

    def test_create_label_uses_default_visibility_and_trimmed_name(self):
        gmail_api = _FakeGmailApi(_FakeMessagesApi(), labels=[])
        self.service.gmail = gmail_api

        created = self.service.create_label("  Newsletter  ")
        labels_api = gmail_api.users().labels()

        self.assertEqual(created["name"], "Newsletter")
        self.assertEqual(created["labelListVisibility"], "labelShow")
        self.assertEqual(created["messageListVisibility"], "show")
        self.assertEqual(labels_api.create_calls[0]["body"]["name"], "Newsletter")

    def test_rename_label_uses_patch_with_trimmed_name(self):
        gmail_api = _FakeGmailApi(
            _FakeMessagesApi(),
            labels=[{"id": "Label_1", "name": "Old Name", "type": "user"}],
        )
        self.service.gmail = gmail_api

        updated = self.service.rename_label("Label_1", "  New Name  ")
        labels_api = gmail_api.users().labels()

        self.assertEqual(updated["name"], "New Name")
        self.assertEqual(labels_api.patch_calls[0]["id"], "Label_1")
        self.assertEqual(labels_api.patch_calls[0]["body"]["name"], "New Name")

    def test_delete_label_calls_delete_endpoint(self):
        gmail_api = _FakeGmailApi(
            _FakeMessagesApi(),
            labels=[{"id": "Label_1", "name": "Cleanup", "type": "user"}],
        )
        self.service.gmail = gmail_api

        deleted = self.service.delete_label("Label_1")
        labels_api = gmail_api.users().labels()

        self.assertTrue(deleted)
        self.assertEqual(labels_api.delete_calls[0]["id"], "Label_1")
        self.assertEqual(labels_api.labels, [])

    def test_label_create_and_rename_reject_empty_names(self):
        self.service.gmail = _FakeGmailApi(_FakeMessagesApi(), labels=[])

        with self.assertRaises(ValueError):
            self.service.create_label("   ")
        with self.assertRaises(ValueError):
            self.service.rename_label("Label_1", "   ")

    def test_process_rule_trashes_matching_messages(self):
        messages_api = _FakeMessagesApi(
            list_responses=[{"messages": [{"id": "m1"}, {"id": "m2"}]}]
        )
        self.service.gmail = _FakeGmailApi(messages_api)
        rule = CleanRule("Spam", "Alle", "sender", "spam@example.com")

        processed = self.service.process_rule(rule, trash=True)

        self.assertEqual(processed, 2)
        self.assertEqual(len(messages_api.trash_calls), 2)
        self.assertEqual(
            messages_api.list_calls[0]["q"],
            'from:"spam@example.com" -label:TRASH',
        )

    def test_drive_cleanup_helpers_call_drive_endpoints(self):
        self.service.drive = _FakeDriveApi({})
        files_api = self.service.drive.files()

        trashed = self.service.trash_drive_file_ids(["drive-1", "drive-2"])
        deleted = self.service.delete_drive_file_ids(["drive-3"])
        restored = self.service.restore_drive_file("drive-4")

        self.assertEqual(trashed, 2)
        self.assertEqual(deleted, 1)
        self.assertTrue(restored)
        self.assertEqual(files_api.update_calls[0]["body"], {"trashed": True})
        self.assertEqual(files_api.update_calls[1]["body"], {"trashed": True})
        self.assertEqual(files_api.update_calls[2]["body"], {"trashed": False})
        self.assertEqual(files_api.delete_calls[0]["fileId"], "drive-3")


if __name__ == "__main__":
    unittest.main()
