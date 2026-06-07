"""
Source-platform smoke for UniversalMailCleaner.
Runs headless on macOS and Linux (QT_QPA_PLATFORM=offscreen).
Exit 0 = all checks passed, Exit 1 = at least one check failed.
"""
import sys
import os
import tempfile
from pathlib import Path

# Ensure project root is on sys.path so modules resolve without install
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS = "✓"
FAIL = "✗"
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    status = PASS if ok else FAIL
    line = f"  [{status}] {name}"
    if detail:
        line += f": {detail}"
    print(line)


def run_checks() -> None:
    # --- Check 1: Non-GUI module imports ---
    try:
        import models  # noqa: F401
        import imap_client  # noqa: F401
        import gmail_service  # noqa: F401
        import profile_exchange  # noqa: F401
        check("Non-GUI imports (models, imap_client, gmail_service, profile_exchange)", True)
    except Exception as exc:
        check("Non-GUI imports", False, str(exc))

    # --- Check 2: PySide6 import ---
    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401
        from PySide6.QtCore import Qt  # noqa: F401
        check("PySide6 import (QApplication, Qt)", True)
    except Exception as exc:
        check("PySide6 import", False, str(exc))

    # --- Check 3: Profile write + read roundtrip with German umlauts ---
    try:
        from models import MailAccount, CleanRule
        from profile_exchange import write_profile, read_profile

        account = MailAccount(name="Büro Köln", host="imap.example.de", user="müller@example.de")
        rule = CleanRule(name="Alte Ü-Mails", target_account="Büro Köln",
                         filter_type="older_than_days", value="90")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            tmp_path = f.name

        try:
            write_profile(tmp_path, [account], [rule], None)
            loaded_accounts, loaded_rules, _ = read_profile(tmp_path)
            assert loaded_accounts[0].name == "Büro Köln", f"name mismatch: {loaded_accounts[0].name!r}"
            assert loaded_rules[0].name == "Alte Ü-Mails", f"rule name mismatch: {loaded_rules[0].name!r}"
            raw = Path(tmp_path).read_text(encoding="utf-8")
            assert "Büro" in raw, "Umlaut not preserved as UTF-8"
            check("Profile write+read roundtrip (umlauts)", True)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except Exception as exc:
        check("Profile write+read roundtrip", False, str(exc))

    # --- Check 4: decode_header_str with encoded header ---
    try:
        from imap_client import decode_header_str
        encoded = "=?utf-8?b?UmVjaG51bmcgZsO8ciBLw7ZsbiBCw7xy?="
        result = decode_header_str(encoded)
        assert isinstance(result, str) and len(result) > 0, f"unexpected: {result!r}"
        check("decode_header_str (encoded header)", True, repr(result))
    except Exception as exc:
        check("decode_header_str", False, str(exc))

    # --- Check 5: MailAccount + CleanRule dict roundtrip ---
    try:
        from models import MailAccount, CleanRule
        acc = MailAccount(name="Privat", host="imap.gmx.net", user="test@gmx.de", port=993)
        rule = CleanRule(name="Spam", target_account="Privat",
                         filter_type="sender", value="spam@junk.de")
        acc2 = MailAccount.from_dict(acc.to_dict())
        rule2 = CleanRule.from_dict(rule.to_dict())
        assert acc2.name == acc.name and acc2.host == acc.host
        assert rule2.value == rule.value
        check("MailAccount + CleanRule dict roundtrip", True)
    except Exception as exc:
        check("MailAccount + CleanRule dict roundtrip", False, str(exc))

    # --- Check 6: Headless MainWindow start ---
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv[:1])
        import mail_imap_cleaner_v1 as m
        win = m.MainWindow()
        assert win is not None
        win.close()
        check("Headless MainWindow start (offscreen)", True)
    except Exception as exc:
        check("Headless MainWindow start", False, str(exc))


def main() -> int:
    print("UniversalMailCleaner source-platform smoke")
    print(f"  Python {sys.version}")
    print(f"  Platform: {sys.platform}")
    print(f"  QT_QPA_PLATFORM={os.environ.get('QT_QPA_PLATFORM', '(not set)')}")
    print()
    run_checks()
    print()
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
