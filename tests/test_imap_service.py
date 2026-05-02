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


if __name__ == "__main__":
    unittest.main()
