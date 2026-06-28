# -*- coding: utf-8 -*-
"""Regressionstests Bugsweep 2026-06-23 (Desktop, /bugsweep-Loop Run 12/15, PARTIAL).

Contained-Fixes (der KRITISCHE MSN-statt-UID-Loeschbug ist bewusst deferred -> AUFGABEN/Ticket):
BS-6: gmail delete_message_ids meldete bei fehlendem Scope still processed=0 statt hart abzuweisen.
BS-7: profile_exchange Account-Import ohne isinstance-Guard -> AttributeError bricht ganzen Import ab.
BS-8: profile_exchange write_profile nicht-atomar -> Datei-Korruption bei Crash.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_gmail_permanent_delete_raises_not_silent():
    s = _read("gmail_service.py")
    seg = s[s.index("def delete_message_ids"):s.index("def trash_drive_file_ids")]
    assert "raise PermissionError" in seg


def test_profile_account_import_isinstance_guard():
    import profile_exchange as pe
    payload = {"schema": pe.PROFILE_SCHEMA, "accounts": ["nicht_dict"], "rules": []}
    with pytest.raises(ValueError):  # vor Fix: AttributeError (anderer Typ)
        pe.load_profile_payload(payload)


def test_profile_write_atomic_source():
    s = _read("profile_exchange.py")
    assert "tmp.replace(p)" in s
    assert "Path(path).write_text(" not in s  # alter nicht-atomarer Pfad ersetzt


def test_worker_task_done_does_not_shadow_qthread_finished():
    """Worker.task_done = Signal(str); QThread.finished bleibt der ererbte parameterlose Lifecycle-Signal."""
    s = _read("workers.py")
    # Altes Shadowing muss weg sein
    assert "finished = Signal" not in s
    # Neuer, eindeutiger Signal-Name muss vorhanden sein
    assert "task_done = Signal(str)" in s
