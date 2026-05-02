"""Reusable scheduler widget (QTimer-based) for periodic mail operations.

Provides ScheduleConfig (dataclass) and SchedulerWidget (QWidget) that
can be embedded in any PySide6 application to trigger recurring tasks.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QCheckBox, QSpinBox, QLabel, QPushButton,
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ScheduleConfig:
    """Persistent configuration for the scheduler."""

    enabled: bool = False
    interval_hours: int = 24
    run_on_startup: bool = False
    last_run: str = ""   # ISO-format timestamp or empty string
    next_run: str = ""   # ISO-format timestamp or empty string (informational)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ScheduleConfig":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------

class SchedulerWidget(QWidget):
    """QWidget that lets the user configure and manually trigger a schedule.

    Emits ``run_requested`` whenever the timer fires or the user clicks
    "Jetzt ausfuehren". The owner connects to this signal and performs
    the actual work.

    Usage::

        scheduler = SchedulerWidget()
        scheduler.run_requested.connect(my_cleanup_slot)
        tab_widget.addTab(scheduler, "Scheduler")

        # Persist config on app close:
        cfg = scheduler.get_config()

        # Restore config on startup:
        scheduler.set_config(saved_cfg)
    """

    run_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = ScheduleConfig()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)

        # --- Configuration group ---
        g_cfg = QGroupBox("Automatisches Cleanup")
        fl = QFormLayout(g_cfg)

        self.chk_enabled = QCheckBox("Scheduler aktivieren")
        self.chk_enabled.toggled.connect(self._on_toggle)
        fl.addRow(self.chk_enabled)

        h_interval = QHBoxLayout()
        self.spin_hours = QSpinBox()
        self.spin_hours.setRange(1, 168)   # 1 h – 1 week
        self.spin_hours.setValue(24)
        self.spin_hours.setSuffix(" Stunden")
        self.spin_hours.valueChanged.connect(self._on_interval_changed)
        h_interval.addWidget(QLabel("Intervall:"))
        h_interval.addWidget(self.spin_hours)
        h_interval.addStretch()
        fl.addRow(h_interval)

        self.chk_startup = QCheckBox("Bei Programmstart pruefen")
        fl.addRow(self.chk_startup)

        lay.addWidget(g_cfg)

        # --- Status group ---
        g_status = QGroupBox("Status")
        fl2 = QFormLayout(g_status)

        self.lbl_last = QLabel("-")
        self.lbl_next = QLabel("-")
        self.lbl_status = QLabel("Inaktiv")
        self.lbl_status.setStyleSheet("color: gray;")

        fl2.addRow("Letzter Lauf:", self.lbl_last)
        fl2.addRow("Naechster Lauf:", self.lbl_next)
        fl2.addRow("Status:", self.lbl_status)

        lay.addWidget(g_status)

        # --- Buttons ---
        h_btn = QHBoxLayout()
        self.btn_run = QPushButton("Jetzt ausfuehren")
        self.btn_run.clicked.connect(self._manual_run)
        h_btn.addWidget(self.btn_run)
        h_btn.addStretch()
        lay.addLayout(h_btn)

        lay.addStretch()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_config(self) -> ScheduleConfig:
        """Return the current configuration as a ScheduleConfig dataclass."""
        return ScheduleConfig(
            enabled=self.chk_enabled.isChecked(),
            interval_hours=self.spin_hours.value(),
            run_on_startup=self.chk_startup.isChecked(),
            last_run=self.config.last_run,
            next_run=self.config.next_run,
        )

    def set_config(self, cfg: ScheduleConfig) -> None:
        """Apply a previously saved ScheduleConfig to the widget."""
        self.config = cfg
        self.chk_enabled.setChecked(cfg.enabled)
        self.spin_hours.setValue(cfg.interval_hours)
        self.chk_startup.setChecked(cfg.run_on_startup)
        if cfg.last_run:
            self.lbl_last.setText(cfg.last_run[:16])
        self._update_timer()

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _on_toggle(self, checked: bool) -> None:
        self.config.enabled = checked
        self._update_timer()

    def _on_interval_changed(self, _value: int) -> None:
        if self.config.enabled:
            self._update_timer()

    def _update_timer(self) -> None:
        if self.config.enabled:
            interval_ms = self.spin_hours.value() * 3600 * 1000
            self._timer.start(interval_ms)
            self.lbl_status.setText("Aktiv")
            self.lbl_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self._calc_next_run()
        else:
            self._timer.stop()
            self.lbl_status.setText("Inaktiv")
            self.lbl_status.setStyleSheet("color: gray;")
            self.lbl_next.setText("-")
            self.config.next_run = ""

    def _calc_next_run(self) -> None:
        if self.config.enabled:
            hours = self.spin_hours.value()
            next_dt = QDateTime.currentDateTime().addSecs(hours * 3600)
            label_text = next_dt.toString("dd.MM.yyyy HH:mm")
            self.lbl_next.setText(label_text)
            self.config.next_run = next_dt.toString("yyyy-MM-ddTHH:mm:ss")

    def _on_timer(self) -> None:
        """Called by QTimer on each interval tick."""
        self.config.last_run = datetime.now().isoformat()
        self.lbl_last.setText(self.config.last_run[:16])
        self._calc_next_run()
        self.run_requested.emit()

    def _manual_run(self) -> None:
        """Called when the user clicks 'Jetzt ausfuehren'."""
        self.config.last_run = datetime.now().isoformat()
        self.lbl_last.setText(self.config.last_run[:16])
        self.run_requested.emit()
