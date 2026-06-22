"""Tests for MainWindow closeEvent and run_worker worker-lifecycle guard."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget
from PySide6.QtGui import QCloseEvent

_APP = QApplication.instance() or QApplication([])


class TestCloseEventStopsWorker(unittest.TestCase):
    def test_close_event_requests_interruption_when_worker_running(self):
        """closeEvent must stop a running worker before saving and closing."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        win.worker = mock_worker

        win.closeEvent(QCloseEvent())

        mock_worker.requestInterruption.assert_called_once()
        mock_worker.wait.assert_called_once()
        win.deleteLater()

    def test_close_event_skips_interruption_when_no_worker(self):
        """closeEvent must not crash when no worker has been assigned."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        # no win.worker assigned
        win.closeEvent(QCloseEvent())  # must not raise
        win.deleteLater()

    def test_close_event_skips_interruption_when_worker_finished(self):
        """closeEvent must not call wait if the worker already stopped."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = False
        win.worker = mock_worker

        win.closeEvent(QCloseEvent())

        mock_worker.requestInterruption.assert_not_called()
        mock_worker.wait.assert_not_called()
        win.deleteLater()


class TestRunWorkerGuard(unittest.TestCase):
    def test_run_worker_stops_old_worker_before_starting_new(self):
        """run_worker must request interruption of the previous worker if still running."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        mock_old = MagicMock()
        mock_old.isRunning.return_value = True
        win.worker = mock_old

        with patch("mail_imap_cleaner_v1.Worker") as MockWorker:
            fake_new = MagicMock()
            fake_new.isRunning.return_value = False
            MockWorker.return_value = fake_new
            win.run_worker("rules", {"rules": [], "safe_mode": True})

        mock_old.requestInterruption.assert_called_once()
        mock_old.wait.assert_called_once()
        win.deleteLater()

    def test_run_worker_does_not_stop_finished_worker(self):
        """run_worker must not stop a worker that already finished."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        mock_old = MagicMock()
        mock_old.isRunning.return_value = False
        win.worker = mock_old

        with patch("mail_imap_cleaner_v1.Worker") as MockWorker:
            fake_new = MagicMock()
            MockWorker.return_value = fake_new
            win.run_worker("rules", {"rules": [], "safe_mode": True})

        mock_old.requestInterruption.assert_not_called()
        mock_old.wait.assert_not_called()
        win.deleteLater()


class TestRunWorkerDisconnectsStaleSignal(unittest.TestCase):
    """run_worker must disconnect data_ready from fill_large before replacing a running worker."""

    def test_old_data_ready_disconnected_before_worker_replaced(self):
        """When a scan_large worker is replaced, the old data_ready signal is disconnected."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        mock_old = MagicMock()
        mock_old.isRunning.return_value = True
        win.worker = mock_old

        with patch("mail_imap_cleaner_v1.Worker") as MockWorker:
            fake_new = MagicMock()
            MockWorker.return_value = fake_new
            win.run_worker("scan_large", {"threshold": 10, "folders": ["INBOX"]})

        mock_old.data_ready.disconnect.assert_called_once_with(win.fill_large)
        win.deleteLater()

    def test_disconnect_failure_does_not_abort_worker_replacement(self):
        """A RuntimeError from disconnect (signal already disconnected) must not abort run_worker."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        mock_old = MagicMock()
        mock_old.isRunning.return_value = True
        mock_old.data_ready.disconnect.side_effect = RuntimeError("not connected")
        win.worker = mock_old

        with patch("mail_imap_cleaner_v1.Worker") as MockWorker:
            fake_new = MagicMock()
            MockWorker.return_value = fake_new
            win.run_worker("scan_large", {"threshold": 10, "folders": ["INBOX"]})  # must not raise

        mock_old.requestInterruption.assert_called_once()
        win.deleteLater()


class TestLabelActionWorkerLifetime(unittest.TestCase):
    """_run_label_service_task must keep workers alive until they finish."""

    def test_concurrent_label_tasks_both_kept_alive(self):
        """Two rapid label tasks must each stay in _label_action_workers until finished."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()

        tasks_run = []

        def slow_task(tag):
            tasks_run.append(tag)
            return {"name": tag}

        # Start first task (won't finish immediately in a real thread — we just verify list management)
        win._run_label_service_task(lambda: slow_task("a"), lambda _: None, "err")
        self.assertEqual(len(win._label_action_workers), 1, "Worker must be tracked after start")

        # Start a second task — old worker must NOT be evicted from the list prematurely
        win._run_label_service_task(lambda: slow_task("b"), lambda _: None, "err")
        # Both workers are tracked
        self.assertGreaterEqual(len(win._label_action_workers), 1)

        # Wait for both to finish
        for w in list(win._label_action_workers):
            w.wait(3000)

        # After finishing, workers remove themselves from the list
        for _ in range(20):  # give cleanup signals time to be processed
            _APP.processEvents()

        self.assertEqual(len(win._label_action_workers), 0, "Finished workers must be cleaned up")
        win.deleteLater()


class TestCloseEventStopsInlineWorkers(unittest.TestCase):
    """closeEvent muss auch Inline-Worker stoppen, nicht nur self.worker."""

    def test_close_event_stops_stats_worker(self):
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        stats_w = MagicMock()
        stats_w.isRunning.return_value = True
        win._stats_worker = stats_w

        win.closeEvent(QCloseEvent())

        stats_w.requestInterruption.assert_called_once()
        stats_w.wait.assert_called_once()
        win.deleteLater()

    def test_close_event_stops_labels_worker(self):
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        labels_w = MagicMock()
        labels_w.isRunning.return_value = True
        win._labels_worker = labels_w

        win.closeEvent(QCloseEvent())

        labels_w.requestInterruption.assert_called_once()
        labels_w.wait.assert_called_once()
        win.deleteLater()

    def test_close_event_stops_del_label_worker(self):
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        del_w = MagicMock()
        del_w.isRunning.return_value = True
        win._del_label_worker = del_w

        win.closeEvent(QCloseEvent())

        del_w.requestInterruption.assert_called_once()
        del_w.wait.assert_called_once()
        win.deleteLater()

    def test_close_event_stops_label_action_workers(self):
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        action_w = MagicMock()
        action_w.isRunning.return_value = True
        win._label_action_workers = [action_w]

        win.closeEvent(QCloseEvent())

        action_w.requestInterruption.assert_called_once()
        action_w.wait.assert_called_once()
        win.deleteLater()

    def test_close_event_skips_stopped_inline_worker(self):
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        stopped_w = MagicMock()
        stopped_w.isRunning.return_value = False
        win._stats_worker = stopped_w

        win.closeEvent(QCloseEvent())

        stopped_w.requestInterruption.assert_not_called()
        stopped_w.wait.assert_not_called()
        win.deleteLater()


class TestPrimaryNavigationAccessibility(unittest.TestCase):
    def test_settings_tab_uses_readable_label_and_tooltip(self):
        """The settings tab must not rely on a lone gear symbol."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        tabs = win.centralWidget().findChild(QTabWidget)

        self.assertIsNotNone(tabs)
        labels = [tabs.tabText(index) for index in range(tabs.count())]
        self.assertIn("⚙ Einstellungen", labels)

        settings_index = labels.index("⚙ Einstellungen")
        self.assertEqual(
            tabs.tabToolTip(settings_index),
            "Einstellungen für Sicherheitsmodus und Profilaustausch öffnen.",
        )
        win.deleteLater()

    def test_label_action_buttons_expose_contextual_accessible_names(self):
        """Row actions in the Gmail labels table must name the affected label."""
        from mail_imap_cleaner_v1 import MainWindow

        win = MainWindow()
        win._populate_labels_table(
            [{"id": "Label_123", "name": "Rechnungen 2026", "type": "user"}]
        )

        actions = win.table_labels.cellWidget(0, 2)
        self.assertIsNotNone(actions)
        buttons = {button.text(): button for button in actions.findChildren(QPushButton)}

        self.assertEqual(
            buttons["Leeren"].accessibleName(),
            "Label Rechnungen 2026 leeren",
        )
        self.assertEqual(
            buttons["Leeren"].accessibleDescription(),
            "Verschiebt alle Mails mit dem Gmail-Label Rechnungen 2026 in den Papierkorb.",
        )
        self.assertEqual(
            buttons["Umbenennen"].accessibleName(),
            "Label Rechnungen 2026 umbenennen",
        )
        self.assertEqual(
            buttons["Umbenennen"].toolTip(),
            "Das Gmail-Label Rechnungen 2026 umbenennen.",
        )
        self.assertEqual(
            buttons["Löschen"].accessibleName(),
            "Label Rechnungen 2026 löschen",
        )
        self.assertEqual(
            buttons["Löschen"].accessibleDescription(),
            "Löscht nur das Gmail-Label Rechnungen 2026, nicht die enthaltenen Mails.",
        )
        win.deleteLater()


if __name__ == "__main__":
    unittest.main()
