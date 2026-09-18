"""Unit tests for the scheduler widget."""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

from scheduler_widget import ScheduleConfig, SchedulerWidget

_APP = QApplication.instance() or QApplication([])


class TestSchedulerWidget(unittest.TestCase):
    def setUp(self):
        self.widget = SchedulerWidget()

    def tearDown(self):
        self.widget.deleteLater()

    def test_set_config_roundtrip_preserves_scheduler_state(self):
        config = ScheduleConfig(
            enabled=True,
            interval_hours=6,
            run_on_startup=True,
            last_run="2026-05-09T10:00:00",
        )

        self.widget.set_config(config)
        current = self.widget.get_config()

        self.assertTrue(current.enabled)
        self.assertEqual(current.interval_hours, 6)
        self.assertTrue(current.run_on_startup)
        self.assertEqual(current.last_run, "2026-05-09T10:00:00")
        self.assertEqual(self.widget.lbl_status.text(), "Aktiv")

    def test_manual_run_updates_last_run_and_emits_signal(self):
        hits = []
        self.widget.run_requested.connect(lambda: hits.append(True))

        self.widget._manual_run()

        self.assertEqual(len(hits), 1)
        self.assertTrue(self.widget.get_config().last_run)
        self.assertNotEqual(self.widget.lbl_last.text(), "-")

    def test_scheduler_controls_expose_accessible_metadata(self):
        """Scheduler controls must provide clear tooltips and accessible names."""
        self.assertEqual(self.widget.chk_enabled.accessibleName(), "Scheduler aktivieren")
        self.assertIn("periodische", self.widget.chk_enabled.toolTip())
        self.assertEqual(self.widget.spin_hours.accessibleName(), "Ausführungsintervall in Stunden")
        self.assertIn("Zeitabstand", self.widget.spin_hours.toolTip())
        self.assertEqual(self.widget.chk_startup.accessibleName(), "Bei Programmstart prüfen")
        self.assertIn("Programmstart", self.widget.chk_startup.toolTip())
        self.assertEqual(self.widget.btn_run.accessibleName(), "Bereinigung jetzt ausführen")
        self.assertIn("sofort", self.widget.btn_run.toolTip())


if __name__ == "__main__":
    unittest.main()
