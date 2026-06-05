"""Tests for secrets-free UniversalMailCleaner profile exchange."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import CleanRule, MailAccount
from profile_exchange import (
    PROFILE_SCHEMA,
    build_profile_payload,
    load_profile_payload,
    read_profile,
    write_profile,
)


class TestProfileExchange(unittest.TestCase):
    def setUp(self):
        self.accounts = [
            MailAccount(
                name="Privat äöü",
                host="imap.gmx.net",
                user="ich@example.de",
                port=993,
                trash_folder="Papierkorb",
                protocol="IMAP",
            ),
            MailAccount(
                name="Gmail",
                host="",
                user="ich@gmail.com",
                port=0,
                trash_folder="",
                protocol="Gmail API",
            ),
        ]
        self.rules = [
            CleanRule(
                name="Newsletter älter",
                target_account="Privat äöü",
                filter_type="older_than_days",
                value="90",
                active=True,
            ),
            CleanRule(
                name="Große Mails",
                target_account="Alle",
                filter_type="size_mb",
                value="25",
                active=False,
            ),
        ]
        self.settings = {
            "safe_mode": False,
            "selected_rule_folders": ["INBOX", "Archiv"],
            "large_item_threshold_mb": 42,
            "scan_mail": True,
            "scan_drive": True,
            "scheduler": {
                "enabled": True,
                "interval_hours": 12,
                "run_on_startup": True,
            },
        }

    def test_build_profile_payload_is_secrets_free(self):
        payload = build_profile_payload(
            self.accounts,
            self.rules,
            self.settings,
            exported_at="2026-06-03T16:00:00+02:00",
        )

        self.assertEqual(payload["schema"], PROFILE_SCHEMA)
        self.assertEqual(payload["accounts"][0]["name"], "Privat äöü")
        self.assertNotIn("password", json.dumps(payload))
        self.assertNotIn("token", json.dumps(payload).lower())
        self.assertEqual(payload["settings"]["selected_rule_folders"], ["INBOX", "Archiv"])
        self.assertEqual(payload["settings"]["scheduler"]["interval_hours"], 12)

    def test_write_profile_uses_utf8_without_ascii_escaping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profil.json"
            write_profile(
                path,
                self.accounts,
                self.rules,
                self.settings,
                exported_at="2026-06-03T16:00:00+02:00",
            )
            raw = path.read_text(encoding="utf-8")

        self.assertIn("Privat äöü", raw)
        self.assertNotIn("\\u00e4", raw)

    def test_read_profile_roundtrip_restores_accounts_rules_and_settings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profil.json"
            write_profile(path, self.accounts, self.rules, self.settings)
            accounts, rules, settings = read_profile(path)

        self.assertEqual([account.name for account in accounts], ["Privat äöü", "Gmail"])
        self.assertEqual([rule.filter_type for rule in rules], ["older_than_days", "size_mb"])
        self.assertEqual(settings["selected_rule_folders"], ["INBOX", "Archiv"])
        self.assertTrue(settings["scheduler"]["run_on_startup"])

    def test_load_profile_payload_rejects_unknown_schema(self):
        with self.assertRaises(ValueError):
            load_profile_payload({"schema": "other-schema", "accounts": [], "rules": []})

    def test_load_profile_payload_handles_null_settings(self):
        payload = {
            "schema": PROFILE_SCHEMA,
            "accounts": [],
            "rules": [],
            "settings": None,
        }
        accounts, rules, settings = load_profile_payload(payload)
        self.assertEqual(settings["selected_rule_folders"], ["INBOX"])

    def test_load_profile_payload_accepts_legacy_rule_aliases(self):
        payload = {
            "schema": PROFILE_SCHEMA,
            "accounts": [{"name": "GMX", "host": "imap.gmx.net", "user": "u", "port": 993}],
            "rules": [
                {
                    "name": "Newsletter",
                    "account": "GMX",
                    "type": "sender",
                    "value": "newsletter@example.org",
                    "active": True,
                    "folders": ["INBOX", "Archiv"],
                }
            ],
            "settings": {"safe_mode": True},
        }

        accounts, rules, settings = load_profile_payload(payload)

        self.assertEqual(accounts[0].name, "GMX")
        self.assertEqual(rules[0].target_account, "GMX")
        self.assertEqual(rules[0].filter_type, "sender")
        self.assertEqual(settings["selected_rule_folders"], ["INBOX", "Archiv"])


if __name__ == "__main__":
    unittest.main()
