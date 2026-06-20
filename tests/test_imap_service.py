"""Unit Tests für ImapService"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Import der zu testenden Module
sys.path.insert(0, str(Path(__file__).parent.parent))
from mail_imap_cleaner_v1 import ImapService, CleanRule


class TestImapServiceSearchCriteria(unittest.TestCase):
    """Tests für ImapService.get_search_criteria()"""

    def setUp(self):
        """Test-Setup: ImapService mit Mock-Log-Funktion erstellen"""
        self.service = ImapService(lambda msg: None)  # Dummy log function

    def test_older_than_days_valid(self):
        """Test: older_than_days mit gültigem Wert (30 Tage)"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="older_than_days",
            value="30"
        )
        result = self.service.get_search_criteria(rule)
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith('(BEFORE "'))
        self.assertTrue(result.endswith('")'))

    def test_older_than_days_format(self):
        """Test: older_than_days generiert korrektes Datumsformat"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="older_than_days",
            value="7"
        )
        result = self.service.get_search_criteria(rule)

        # Erwartetes Datum berechnen
        expected_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        expected = f'(BEFORE "{expected_date}")'

        self.assertEqual(result, expected)

    def test_sender_filter(self):
        """Test: sender Filter mit E-Mail-Adresse"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="sender",
            value="spam@example.com"
        )
        result = self.service.get_search_criteria(rule)
        self.assertEqual(result, '(FROM "spam@example.com")')

    def test_subject_filter(self):
        """Test: subject Filter mit Suchtext"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="subject",
            value="Newsletter"
        )
        result = self.service.get_search_criteria(rule)
        self.assertEqual(result, '(SUBJECT "Newsletter")')

    def test_size_mb_filter_integer(self):
        """Test: size_mb Filter mit Integer-Wert (10 MB)"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="size_mb",
            value="10"
        )
        result = self.service.get_search_criteria(rule)
        expected_bytes = 10 * 1024 * 1024
        self.assertEqual(result, f'(LARGER {expected_bytes})')

    def test_size_mb_filter_float(self):
        """Test: size_mb Filter mit Float-Wert (5.5 MB)"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="size_mb",
            value="5.5"
        )
        result = self.service.get_search_criteria(rule)
        expected_bytes = int(5.5 * 1024 * 1024)
        self.assertEqual(result, f'(LARGER {expected_bytes})')

    def test_sender_filter_escapes_backslash(self):
        """Test: sender Filter mit Backslash wird RFC-3501-konform escaped"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="sender",
            value="user\\domain"
        )
        result = self.service.get_search_criteria(rule)
        self.assertEqual(result, '(FROM "user\\\\domain")')

    def test_subject_filter_escapes_backslash(self):
        """Test: subject Filter mit Backslash wird RFC-3501-konform escaped"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="subject",
            value="test\\value"
        )
        result = self.service.get_search_criteria(rule)
        self.assertEqual(result, '(SUBJECT "test\\\\value")')

    def test_invalid_filter_type(self):
        """Test: Ungültiger filter_type sollte None zurückgeben"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="invalid_type",
            value="test"
        )
        result = self.service.get_search_criteria(rule)
        self.assertIsNone(result)

    def test_invalid_value_older_than_days(self):
        """Test: Ungültiger Wert bei older_than_days (nicht numerisch)"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="older_than_days",
            value="not_a_number"
        )
        result = self.service.get_search_criteria(rule)
        self.assertIsNone(result)

    def test_invalid_value_size_mb(self):
        """Test: Ungültiger Wert bei size_mb (nicht numerisch)"""
        rule = CleanRule(
            name="Test",
            target_account="Alle",
            filter_type="size_mb",
            value="not_a_number"
        )
        result = self.service.get_search_criteria(rule)
        self.assertIsNone(result)


class TestListFoldersParsing(unittest.TestCase):
    """list_folders must return complete folder names even when they contain spaces."""

    def _make_service_with_folders(self, raw_entries):
        """Return an ImapService whose conn.list() yields the given raw_entries."""
        class _FakeConn:
            def list(inner_self):  # noqa: N805
                return "OK", [
                    e if isinstance(e, bytes) else e.encode()
                    for e in raw_entries
                ]

        service = ImapService(lambda _: None)
        service.conn = _FakeConn()
        return service

    def test_single_word_quoted_folder(self):
        service = self._make_service_with_folders([
            '(\\HasNoChildren) "/" "INBOX"',
            '(\\HasNoChildren) "/" "Sent"',
        ])
        self.assertEqual(service.list_folders(), ["INBOX", "Sent"])

    def test_multi_word_quoted_folder_name(self):
        """Folder names with spaces (e.g. Exchange 'Sent Items') must not be truncated."""
        service = self._make_service_with_folders([
            '(\\HasNoChildren) "/" "Sent Items"',
            '(\\HasNoChildren) "/" "Deleted Items"',
        ])
        self.assertEqual(service.list_folders(), ["Sent Items", "Deleted Items"])

    def test_unquoted_folder_name(self):
        service = self._make_service_with_folders(['(\\HasNoChildren) "/" INBOX'])
        self.assertEqual(service.list_folders(), ["INBOX"])

    def test_empty_entry_is_skipped(self):
        service = self._make_service_with_folders([b"", '(\\HasNoChildren) "/" "INBOX"'])
        self.assertEqual(service.list_folders(), ["INBOX"])


class TestFindTrashFolderParsing(unittest.TestCase):
    """find_trash_folder must correctly detect unquoted and quoted trash folder names."""

    def _make_service_with_account_and_folders(self, raw_entries):
        from models import MailAccount

        class _FakeConn:
            def list(inner_self):  # noqa: N805
                return "OK", [
                    e if isinstance(e, bytes) else e.encode()
                    for e in raw_entries
                ]

        acc = MailAccount(name="Test", host="imap.example.com", user="u@example.com", port=993)
        service = ImapService(lambda _: None)
        service.conn = _FakeConn()
        service.current_account = acc
        return service

    def test_detects_unquoted_papierkorb(self):
        """Unquoted 'Papierkorb' must be detected as trash folder."""
        service = self._make_service_with_account_and_folders([
            '(\\HasNoChildren) "/" INBOX',
            '(\\HasNoChildren) "/" Papierkorb',
            '(\\HasNoChildren) "/" Sent',
        ])
        result = service.find_trash_folder()
        self.assertEqual(result, "Papierkorb")

    def test_detects_quoted_trash(self):
        """Quoted 'Trash' must be detected as trash folder."""
        service = self._make_service_with_account_and_folders([
            '(\\HasNoChildren) "/" "INBOX"',
            '(\\HasNoChildren) "/" "Trash"',
        ])
        result = service.find_trash_folder()
        self.assertEqual(result, "Trash")

    def test_detects_quoted_deleted_items(self):
        """Quoted 'Deleted Items' (Exchange) must be detected as trash folder."""
        service = self._make_service_with_account_and_folders([
            '(\\HasNoChildren) "/" "INBOX"',
            '(\\HasNoChildren) "/" "Deleted Items"',
        ])
        result = service.find_trash_folder()
        self.assertEqual(result, "Deleted Items")

    def test_falls_back_to_trash_when_no_candidate_matches(self):
        """If no known trash folder is found, 'Trash' is returned as fallback."""
        service = self._make_service_with_account_and_folders([
            '(\\HasNoChildren) "/" INBOX',
            '(\\HasNoChildren) "/" Sent',
        ])
        result = service.find_trash_folder()
        self.assertEqual(result, "Trash")


class TestImapConnectTimeout(unittest.TestCase):
    """ImapService.connect() muss IMAP4_SSL mit timeout=30 aufrufen."""

    def test_connect_passes_timeout_to_imap4_ssl(self):
        import imap_client as ic
        from models import MailAccount

        calls = []

        class FakeIMAP:
            def __init__(self, host, port, timeout=None):
                calls.append({"host": host, "port": port, "timeout": timeout})

            def login(self, user, pwd):
                pass

        original_imap = ic.imaplib.IMAP4_SSL
        ic.imaplib.IMAP4_SSL = FakeIMAP
        original_keyring_avail = ic.KEYRING_AVAIL
        ic.KEYRING_AVAIL = True

        import keyring as _keyring
        original_get_password = _keyring.get_password
        _keyring.get_password = lambda app, name: "geheimwort"

        try:
            acc = MailAccount(name="Test", host="imap.example.com", user="u@test.com", port=993)
            service = ic.ImapService(lambda _: None)
            service.connect(acc)
        finally:
            ic.imaplib.IMAP4_SSL = original_imap
            ic.KEYRING_AVAIL = original_keyring_avail
            _keyring.get_password = original_get_password

        self.assertTrue(calls, "IMAP4_SSL wurde nicht aufgerufen")
        self.assertEqual(calls[0]["timeout"], 30, f"timeout war {calls[0]['timeout']}, erwartet 30")


if __name__ == "__main__":
    unittest.main()
