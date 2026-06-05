"""Unit tests for backend selection in Worker."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import QCoreApplication

from models import CleanRule, MailAccount
from workers import Worker

_APP = QCoreApplication.instance() or QCoreApplication([])


class _FakeGmailService:
    instances = []

    def __init__(self, *args, **kwargs):
        self.auth_called = False
        self.process_rule_calls = []
        self.scan_calls = []
        self.drive_scan_calls = []
        self.trash_calls = []
        self.delete_calls = []
        self.restore_calls = []
        self.drive_trash_calls = []
        self.drive_delete_calls = []
        self.drive_restore_calls = []
        _FakeGmailService.instances.append(self)

    def auth(self):
        self.auth_called = True
        return True

    def process_rule(self, rule, trash=True):
        self.process_rule_calls.append((rule.name, trash))
        return 3

    def scan_large_messages(self, threshold_mb):
        self.scan_calls.append(threshold_mb)
        return [{
            "id": "gmail-1",
            "folder": "Gmail",
            "subject": "Large Mail",
            "size": 12.5,
            "date": "2026-05-09 10:00",
            "item_type": "gmail_message",
        }]

    def scan_large_drive_files(self, threshold_mb):
        self.drive_scan_calls.append(threshold_mb)
        return [{
            "id": "drive-1",
            "folder": "Drive",
            "subject": "Archive.zip",
            "size": 18.0,
            "date": "2026-05-18 09:30",
            "item_type": "drive_file",
        }]

    def trash_message_ids(self, ids):
        self.trash_calls.append(list(ids))
        return len(ids)

    def delete_message_ids(self, ids):
        self.delete_calls.append(list(ids))
        return len(ids)

    def restore_mail(self, msg_id):
        self.restore_calls.append(msg_id)
        return True

    def trash_drive_file_ids(self, ids):
        self.drive_trash_calls.append(list(ids))
        return len(ids)

    def delete_drive_file_ids(self, ids):
        self.drive_delete_calls.append(list(ids))
        return len(ids)

    def restore_drive_file(self, file_id):
        self.drive_restore_calls.append(file_id)
        return True


class _FakeImapConn:
    def __init__(self):
        self.select_calls = []
        self.copy_calls = []
        self.store_calls = []
        self.expunge_calls = 0

    def select(self, mailbox, readonly=False):
        self.select_calls.append((mailbox, readonly))
        return "OK", [b""]

    def copy(self, message_set, mailbox):
        self.copy_calls.append((message_set, mailbox))
        return "OK", [b""]

    def store(self, *args):
        self.store_calls.append(args)
        return "OK", [b""]

    def expunge(self):
        self.expunge_calls += 1
        return "OK", [b""]


class _FakeImapService:
    instances = []

    def __init__(self, log_func):
        self.log = log_func
        self.conn = _FakeImapConn()
        self.connected_account = None
        self.disconnect_called = False
        _FakeImapService.instances.append(self)

    def connect(self, account):
        self.connected_account = account
        return True

    def find_trash_folder(self):
        return "Trash"

    def disconnect(self):
        self.disconnect_called = True


class TestWorkerBackends(unittest.TestCase):
    def setUp(self):
        _FakeGmailService.instances.clear()
        self.gmail_account = MailAccount(
            name="Gmail Main",
            host="",
            user="user@gmail.com",
            port=0,
            protocol="Gmail API",
        )

    def test_rules_use_gmail_backend_for_gmail_accounts(self):
        rule = CleanRule("Old", "Gmail Main", "older_than_days", "30")

        with patch("workers.GmailService", _FakeGmailService):
            worker = Worker("rules", {"rules": [rule], "safe_mode": True}, [self.gmail_account])
            worker.run()

        fake = _FakeGmailService.instances[-1]
        self.assertTrue(fake.auth_called)
        self.assertEqual(fake.process_rule_calls, [("Old", True)])

    def test_scan_large_emits_gmail_and_drive_results(self):
        received = []

        with patch("workers.GmailService", _FakeGmailService):
            worker = Worker(
                "scan_large",
                {
                    "threshold": 15,
                    "target_account": "Gmail Main",
                    "scan_mail": True,
                    "scan_drive": True,
                },
                [self.gmail_account],
            )
            worker.data_ready.connect(lambda items: received.extend(items))
            worker.run()

        fake = _FakeGmailService.instances[-1]
        self.assertEqual(fake.scan_calls, [15])
        self.assertEqual(fake.drive_scan_calls, [15])
        self.assertEqual(len(received), 2)
        self.assertEqual(received[0]["account"], "Gmail Main")
        self.assertEqual(received[0]["folder"], "Gmail")
        self.assertEqual(received[1]["folder"], "Drive")

    def test_delete_and_undo_use_gmail_and_drive_backends(self):
        items = [
            {"account": "Gmail Main", "id": "msg-1", "item_type": "gmail_message"},
            {"account": "Gmail Main", "id": "drive-1", "item_type": "drive_file"},
        ]

        with patch("workers.GmailService", _FakeGmailService):
            delete_worker = Worker("delete", {"items": items, "safe_mode": True}, [self.gmail_account])
            delete_worker.run()
            undo_worker = Worker("undo", {"items": items, "safe_mode": True}, [self.gmail_account])
            undo_worker.run()

        delete_fake = _FakeGmailService.instances[0]
        undo_fake = _FakeGmailService.instances[1]
        self.assertEqual(delete_fake.trash_calls, [["msg-1"]])
        self.assertEqual(delete_fake.drive_trash_calls, [["drive-1"]])
        self.assertEqual(undo_fake.restore_calls, ["msg-1"])
        self.assertEqual(undo_fake.drive_restore_calls, ["drive-1"])

    def test_undo_restores_imap_items_to_their_original_folders(self):
        items = [
            {"account": "IMAP Main", "id": "msg-1", "folder": "Projects"},
            {"account": "IMAP Main", "id": "msg-2", "folder": "INBOX"},
            {"account": "IMAP Main", "id": "msg-3", "folder": "Projects"},
        ]
        imap_account = MailAccount(
            name="IMAP Main",
            host="imap.example.com",
            user="user@example.com",
            port=993,
            protocol="IMAP",
        )

        with patch("workers.ImapService", _FakeImapService):
            worker = Worker("undo", {"items": items, "safe_mode": True}, [imap_account])
            worker.run()

        fake = _FakeImapService.instances[-1]
        self.assertEqual(fake.conn.select_calls, [("Trash", False)])
        self.assertEqual(
            fake.conn.copy_calls,
            [("msg-1,msg-3", "Projects"), ("msg-2", "INBOX")],
        )
        self.assertEqual(len(fake.conn.store_calls), 2)
        self.assertEqual(fake.conn.expunge_calls, 2)


class TestScanLargeMissingDateHeader(unittest.TestCase):
    """scan_large must not crash when an email has no Date header."""

    def test_missing_date_header_yields_empty_date_string(self):
        raw_headers = b"Subject: Big Attachment\r\n\r\n"
        size = 15_000_000
        meta = (
            f"1 (RFC822.SIZE {size} BODY[HEADER.FIELDS (SUBJECT DATE)] "
            f"{{{len(raw_headers)}}})"
        ).encode()

        class _Conn:
            def select(self, folder, readonly=False):
                return "OK", [b"1"]

            def search(self, charset, criteria):
                return "OK", [b"1"]

            def fetch(self, num, parts):
                return "OK", [(meta, raw_headers), b")"]

        class _Svc:
            def __init__(self, log_func):
                self.conn = _Conn()

            def connect(self, account):
                return True

            def disconnect(self):
                pass

        imap_account = MailAccount(
            name="IMAP Test",
            host="imap.example.com",
            user="test@example.com",
            port=993,
        )

        received = []
        with patch("workers.ImapService", _Svc):
            worker = Worker(
                "scan_large",
                {"threshold": 10, "folders": ["INBOX"], "scan_mail": True},
                [imap_account],
            )
            worker.data_ready.connect(lambda items: received.extend(items))
            worker.run()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["date"], "")


if __name__ == "__main__":
    unittest.main()
