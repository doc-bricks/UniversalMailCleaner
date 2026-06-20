"""Universal Mail Cleaner - IMAP-based email cleanup tool.

Provides a PyQt6 GUI application for managing and cleaning emails
from multiple IMAP accounts. Supports rule-based deletion, large
email scanning, and safe trash-based removal.

Usage:
    python mail_imap_cleaner_v1.py

Modules:
    models.py      -- Data classes (MailAccount, CleanRule)
    imap_client.py -- IMAP connection logic (ImapService, decode_header_str)
    workers.py     -- Background worker thread (Worker)
"""
import sys
import json
import os
import logging
import imaplib
import email
import email.header
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Callable

# Import from modules
from models import MailAccount, CleanRule
from imap_client import ImapService, decode_header_str
from profile_exchange import (
    default_profile_settings,
    merge_profile_settings,
    read_profile,
    write_profile,
)
from workers import Worker

# GUI Imports
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
                             QFormLayout, QPlainTextEdit, QComboBox, QGroupBox,
                             QCheckBox, QTabWidget, QDialogButtonBox,
                             QSpinBox, QMenu, QTreeWidget, QTreeWidgetItem, QLineEdit,
                             QFileDialog,
                             QInputDialog)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QSignalBlocker
from PySide6.QtGui import QDesktopServices, QColor, QPalette

# Security
try:
    import keyring
    KEYRING_AVAIL = True
except ImportError:
    KEYRING_AVAIL = False

# ==================== CONFIGURATION ====================

APP_NAME = "UniversalMailCleaner"
BASE_DIR = Path.home() / ".mail_cleaner"
BASE_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = BASE_DIR / "config.json"

_log_level_name = os.environ.get("UMAIL_CLEANER_LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_name, None)
if not isinstance(_log_level, int):
    print(f"[WARNING] Invalid log level '{_log_level_name}', falling back to INFO.")
    _log_level = logging.INFO

logging.basicConfig(level=_log_level, format="%(asctime)s - %(message)s")
logger = logging.getLogger(APP_NAME)

# ==================== IMAP LOGIC ====================
# (Models imported from models.py; ImapService from imap_client.py; Worker from workers.py)

# ImapService, Worker, decode_header_str moved to imap_client.py and workers.py


class AccountDialog(QDialog):
    """Dialog for creating or editing an IMAP account."""

    def __init__(self, acc=None, parent=None):
        """Initializes the account dialog.

        Args:
            acc: Existing MailAccount to edit, or None to create new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Account" if acc else "New Account")
        l = QFormLayout(self)

        self.n = QLineEdit(acc.name if acc else "")
        self.h = QLineEdit(acc.host if acc else "imap.gmx.net")
        self.u = QLineEdit(acc.user if acc else "")
        self.p = QSpinBox(); self.p.setRange(1, 65535); self.p.setValue(acc.port if acc else 993)
        self.pf = QLineEdit(); self.pf.setEchoMode(QLineEdit.EchoMode.Password)
        self.pf.setPlaceholderText("Leave empty to keep existing" if acc else "")

        l.addRow("Name (Internal):", self.n)
        l.addRow("IMAP Host:", self.h)
        l.addRow("Port:", self.p)
        l.addRow("User/Email:", self.u)
        l.addRow("Password:", self.pf)

        info = QLabel("<i>Note: For Gmail use an 'App Password'!</i>")
        info.setStyleSheet("color: gray")
        l.addRow(info)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        l.addRow(bb)

    def get_account(self):
        """Returns the account data entered in the dialog.

        Returns:
            Tuple of (MailAccount, password_string).
        """
        return MailAccount(self.n.text(), self.h.text(), self.u.text(), self.p.value()), self.pf.text()

class GmailAccountDialog(QDialog):
    """Dialog for adding a Gmail API account (OAuth2)."""

    def __init__(self, acc=None, parent=None):
        """Initialises the Gmail account dialog.

        Args:
            acc:    Existing MailAccount with protocol=='Gmail API' to edit,
                    or None to create new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Gmail API Account bearbeiten" if acc else "Gmail API Account hinzufügen")
        l = QFormLayout(self)

        self.n = QLineEdit(acc.name if acc else "")
        self.u = QLineEdit(acc.user if acc else "")

        l.addRow("Name (intern):", self.n)
        l.addRow("E-Mail-Adresse:", self.u)

        info = QLabel(
            "<i>Authentifizierung via OAuth2 (Browser).<br>"
            "Lege <b>credentials.json</b> neben diese Anwendung,<br>"
            "bevor du den Account verwendest.</i>"
        )
        info.setStyleSheet("color: gray")
        info.setWordWrap(True)
        l.addRow(info)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        l.addRow(bb)

    def get_account(self):
        """Returns the MailAccount created from the dialog inputs.

        Returns:
            MailAccount with protocol='Gmail API'. No password is needed.
        """
        return MailAccount(
            name=self.n.text(),
            host="",
            user=self.u.text(),
            port=0,
            protocol="Gmail API",
        )


class FolderSelectDialog(QDialog):
    """Dialog for selecting IMAP folders to include in rule processing."""

    def __init__(self, accounts: list, parent=None):
        """Initializes the folder selection dialog.

        Args:
            accounts: List of MailAccount objects to choose from.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Select Folders")
        self.setMinimumWidth(350)
        self.accounts = accounts
        self.checkboxes: List[QCheckBox] = []
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Account:"))
        self.cb_acc = QComboBox()
        self.cb_acc.addItems([a.name for a in accounts])
        self.cb_acc.currentIndexChanged.connect(self._load_folders)
        layout.addWidget(self.cb_acc)

        layout.addWidget(QLabel("Folders (select all to include):"))
        self.folder_widget = QWidget()
        self.folder_layout = QVBoxLayout(self.folder_widget)
        self.folder_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.folder_widget)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

        if accounts:
            self._load_folders()

    def _load_folders(self):
        """Connects to the selected account and populates folder checkboxes."""
        for cb in self.checkboxes:
            cb.setParent(None)
        self.checkboxes.clear()

        acc_name = self.cb_acc.currentText()
        acc = next((a for a in self.accounts if a.name == acc_name), None)
        if not acc:
            return

        service = ImapService(lambda msg: None)
        if service.connect(acc):
            folders = service.list_folders()
            service.disconnect()
        else:
            folders = ["INBOX"]

        for folder in folders:
            chk = QCheckBox(folder)
            chk.setChecked(folder == "INBOX")
            self.folder_layout.addWidget(chk)
            self.checkboxes.append(chk)

    def get_selected_folders(self) -> list:
        """Returns the list of checked folder names."""
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


class RuleDialog(QDialog):
    """Dialog for creating or editing a cleanup rule."""

    def __init__(self, rule=None, accounts=[], parent=None):
        """Initializes the rule dialog.

        Args:
            rule: Existing CleanRule to edit, or None to create new.
            accounts: List of available MailAccount objects for the dropdown.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Rule" if rule else "New Rule")
        l = QFormLayout(self)

        self.n = QLineEdit(rule.name if rule else "")
        self.cb_acc = QComboBox(); self.cb_acc.addItems(["Alle"] + [a.name for a in accounts])
        if rule: self.cb_acc.setCurrentText(rule.target_account)

        self.cb_type = QComboBox()
        self.cb_type.addItems(["older_than_days", "subject", "sender", "size_mb"])
        if rule: self.cb_type.setCurrentText(rule.filter_type)

        self.val = QLineEdit(rule.value if rule else "")
        self.val.setPlaceholderText("Days (int), text, or MB")

        self.chk = QCheckBox("Active"); self.chk.setChecked(rule.active if rule else True)

        l.addRow("Name:", self.n)
        l.addRow("Account:", self.cb_acc)
        l.addRow("Type:", self.cb_type)
        l.addRow("Value:", self.val)
        l.addRow(self.chk)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        l.addRow(bb)

    def get_rule(self):
        """Returns the rule data entered in the dialog.

        Returns:
            CleanRule with values from the form fields.
        """
        return CleanRule(self.n.text(), self.cb_acc.currentText(), self.cb_type.currentText(), self.val.text(), self.chk.isChecked())

# ==================== MAIN WINDOW ====================

class MainWindow(QMainWindow):
    """Main application window for Universal Mail Cleaner."""

    def __init__(self):
        """Initializes the main window, loads config, and sets up the UI."""
        super().__init__()
        self.settings = default_profile_settings()
        self.accounts: List[MailAccount] = []
        self.rules: List[CleanRule] = []
        self.selected_rule_folders: List[str] = ["INBOX"]
        self.load_config()
        self.setup_ui()
        # run_on_startup: fire cleanup once after event loop starts
        if (hasattr(self, "_scheduler")
                and self._scheduler.config.run_on_startup
                and self._scheduler.config.enabled):
            from PySide6.QtCore import QTimer as _QTimer
            _QTimer.singleShot(0, self._on_scheduler_run)

    def load_config(self):
        """Loads accounts, rules, and settings from the JSON config file."""
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.settings = merge_profile_settings(data.get("settings"))
                self.accounts = [MailAccount.from_dict(x) for x in data.get("accounts", [])]
                self.rules = [CleanRule.from_dict(x) for x in data.get("rules", [])]
                self.selected_rule_folders = list(
                    self.settings.get("selected_rule_folders", ["INBOX"])
                )
            except Exception as e:
                logger.warning(f"load_config error: {e}")

    def save_config(self):
        """Saves accounts, rules, and settings to the JSON config file."""
        self._sync_settings_from_ui()
        data = {
            "settings": self.settings,
            "accounts": [a.to_dict() for a in self.accounts],
            "rules": [r.to_dict() for r in self.rules]
        }
        try:
            CONFIG_FILE.write_text(
                json.dumps(data, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error("save_config failed: %s", exc)

    def _sync_settings_from_ui(self):
        """Copy relevant UI state back into the persisted settings dict."""
        if hasattr(self, "chk_safe"):
            self.settings["safe_mode"] = self.chk_safe.isChecked()
        self.settings["selected_rule_folders"] = list(self.selected_rule_folders or ["INBOX"])
        if hasattr(self, "spin_mb"):
            self.settings["large_item_threshold_mb"] = self.spin_mb.value()
        if hasattr(self, "chk_scan_mail"):
            self.settings["scan_mail"] = self.chk_scan_mail.isChecked()
        if hasattr(self, "chk_scan_drive"):
            self.settings["scan_drive"] = self.chk_scan_drive.isChecked()
        if hasattr(self, "_scheduler"):
            scheduler_cfg = self._scheduler.get_config()
            self.settings["scheduler"] = {
                "enabled": scheduler_cfg.enabled,
                "interval_hours": scheduler_cfg.interval_hours,
                "run_on_startup": scheduler_cfg.run_on_startup,
                "last_run": scheduler_cfg.last_run,
                "next_run": scheduler_cfg.next_run,
            }
        self.settings = merge_profile_settings(self.settings)

    def _apply_settings_to_ui(self):
        """Apply persisted settings to the current widgets without recursive saves."""
        self.selected_rule_folders = list(
            self.settings.get("selected_rule_folders", ["INBOX"])
        )
        blockers = []
        if hasattr(self, "chk_safe"):
            blockers.append(QSignalBlocker(self.chk_safe))
            self.chk_safe.setChecked(self.settings.get("safe_mode", True))
        if hasattr(self, "spin_mb"):
            blockers.append(QSignalBlocker(self.spin_mb))
            self.spin_mb.setValue(self.settings.get("large_item_threshold_mb", 10))
        if hasattr(self, "chk_scan_mail"):
            blockers.append(QSignalBlocker(self.chk_scan_mail))
            self.chk_scan_mail.setChecked(self.settings.get("scan_mail", True))
        if hasattr(self, "chk_scan_drive"):
            blockers.append(QSignalBlocker(self.chk_scan_drive))
            self.chk_scan_drive.setChecked(self.settings.get("scan_drive", False))
        if hasattr(self, "_scheduler"):
            from scheduler_widget import ScheduleConfig

            self._scheduler.set_config(
                ScheduleConfig.from_dict(self.settings.get("scheduler", {}))
            )
        self.update_mode_label()

    def setup_ui(self):
        """Builds the main window UI with tabs for accounts, rules, large emails, settings, and log."""
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 750)

        # Dark theme
        p = self.palette()
        p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        self.setPalette(p)

        cw = QWidget(); self.setCentralWidget(cw); lay = QVBoxLayout(cw)
        h = QHBoxLayout(); h.addWidget(QLabel("<h2>🧹 Universal Mail Cleaner</h2>")); h.addStretch()
        self.lbl_mode = QLabel(); self.update_mode_label(); h.addWidget(self.lbl_mode); lay.addLayout(h)

        tabs = QTabWidget()

        # TAB 1: ACCOUNTS
        t_acc = QWidget(); l_acc = QVBoxLayout(t_acc)
        self.list_acc = QTableWidget(0, 3)
        self.list_acc.setHorizontalHeaderLabels(["Name", "Host", "User"])
        self.list_acc.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        l_acc.addWidget(self.list_acc)
        h_acc = QHBoxLayout()
        b_add_a = QPushButton("➕ Account"); b_add_a.clicked.connect(self.add_acc)
        b_add_gmail = QPushButton("➕ Gmail API"); b_add_gmail.clicked.connect(self.add_gmail_acc)
        b_del_a = QPushButton("❌ Delete"); b_del_a.clicked.connect(self.del_acc)
        h_acc.addWidget(b_add_a); h_acc.addWidget(b_add_gmail); h_acc.addWidget(b_del_a); h_acc.addStretch()
        l_acc.addLayout(h_acc)
        tabs.addTab(t_acc, "🔑 Accounts")

        # TAB 2: RULES
        t1 = QWidget(); l1 = QVBoxLayout(t1)
        self.tree_rules = QTreeWidget()
        self.tree_rules.setHeaderLabels(["Rule", "Account", "Type", "Value", "Active"])
        self.tree_rules.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_rules.customContextMenuRequested.connect(self.rules_ctx)
        l1.addWidget(self.tree_rules)
        h_rules = QHBoxLayout()
        b_new = QPushButton("➕ Rule"); b_new.clicked.connect(self.add_rule)
        b_folders = QPushButton("📂 Folders..."); b_folders.clicked.connect(self.select_rule_folders)
        b_run = QPushButton("▶️ Run Selected"); b_run.clicked.connect(self.run_selected_rules)
        b_run_all = QPushButton("▶️ Run ALL Rules"); b_run_all.setStyleSheet("background-color: #27ae60; color: white;")
        b_run_all.clicked.connect(self.run_all_rules)
        h_rules.addWidget(b_new); h_rules.addStretch(); h_rules.addWidget(b_folders); h_rules.addWidget(b_run); h_rules.addWidget(b_run_all)
        l1.addLayout(h_rules)
        tabs.addTab(t1, "Auto Rules")

        # TAB 3: LARGE EMAILS
        t2 = QWidget(); l2 = QVBoxLayout(t2)
        conf_grp = QGroupBox("Scan Settings")
        cl = QHBoxLayout(conf_grp)
        self.spin_mb = QSpinBox(); self.spin_mb.setRange(1, 1000); self.spin_mb.setValue(self.settings.get("large_item_threshold_mb", 10)); self.spin_mb.setSuffix(" MB")
        self.spin_mb.valueChanged.connect(self.save_settings_ui)
        self.cb_scan_acc = QComboBox()
        self.chk_scan_mail = QCheckBox("Emails")
        self.chk_scan_mail.setChecked(self.settings.get("scan_mail", True))
        self.chk_scan_mail.toggled.connect(self.save_settings_ui)
        self.chk_scan_drive = QCheckBox("Drive files (Gmail API)")
        self.chk_scan_drive.setToolTip("Only Gmail API accounts can scan Google Drive files.")
        self.chk_scan_drive.setChecked(self.settings.get("scan_drive", False))
        self.chk_scan_drive.toggled.connect(self.save_settings_ui)
        btn_scan = QPushButton("🔍 Start Scan"); btn_scan.clicked.connect(self.start_large_scan)
        cl.addWidget(QLabel("Account:")); cl.addWidget(self.cb_scan_acc)
        cl.addWidget(QLabel("Larger than:")); cl.addWidget(self.spin_mb)
        cl.addWidget(QLabel("Sources:")); cl.addWidget(self.chk_scan_mail); cl.addWidget(self.chk_scan_drive)
        cl.addWidget(btn_scan)
        l2.addWidget(conf_grp)
        self.table_large = QTableWidget(0, 5)
        self.table_large.setHorizontalHeaderLabels(["", "Account", "Subject / File", "Size (MB)", "Date"])
        self.table_large.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        l2.addWidget(self.table_large)
        btn_row = QHBoxLayout()
        b_del_sel = QPushButton("🗑️ Delete Selected"); b_del_sel.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        b_del_sel.clicked.connect(self.delete_selected)
        self.b_undo = QPushButton("↩️ Letzte Aktion rückgängig")
        self.b_undo.setEnabled(False)
        self.b_undo.clicked.connect(self.undo_last_action)
        btn_row.addWidget(b_del_sel)
        btn_row.addWidget(self.b_undo)
        btn_row.addStretch()
        l2.addLayout(btn_row)
        self._undo_history: list = []
        tabs.addTab(t2, "Large Items")

        # TAB 4: SETTINGS
        t3 = QWidget(); l3 = QVBoxLayout(t3)
        g_safe = QGroupBox("Security")
        fl = QFormLayout(g_safe)
        self.chk_safe = QCheckBox("Move to trash (Safe mode)")
        self.chk_safe.setChecked(self.settings.get("safe_mode", True))
        self.chk_safe.toggled.connect(self.save_settings_ui)
        fl.addRow(self.chk_safe)
        l3.addWidget(g_safe)
        g_profile = QGroupBox("Profil austauschen")
        h_profile = QHBoxLayout(g_profile)
        b_export_profile = QPushButton("Profil exportieren...")
        b_export_profile.clicked.connect(self.export_profile)
        b_import_profile = QPushButton("Profil importieren...")
        b_import_profile.clicked.connect(self.import_profile)
        h_profile.addWidget(b_export_profile)
        h_profile.addWidget(b_import_profile)
        h_profile.addStretch()
        l3.addWidget(g_profile)
        if not KEYRING_AVAIL:
            l3.addWidget(QLabel("⚠️ Keyring missing! Passwords will not be saved."))
        l3.addStretch()
        settings_tab_index = tabs.addTab(t3, "⚙ Einstellungen")
        tabs.setTabToolTip(
            settings_tab_index,
            "Einstellungen für Sicherheitsmodus und Profilaustausch öffnen.",
        )

        # TAB 5: SCHEDULER
        from scheduler_widget import SchedulerWidget, ScheduleConfig
        t_sched = QWidget(); l_sched = QVBoxLayout(t_sched)
        self._scheduler = SchedulerWidget()
        self._scheduler.run_requested.connect(self._on_scheduler_run)
        # Restore persisted scheduler config if available
        sched_data = self.settings.get("scheduler")
        if sched_data:
            try:
                self._scheduler.set_config(ScheduleConfig.from_dict(sched_data))
            except Exception:
                pass
        l_sched.addWidget(self._scheduler)
        tabs.addTab(t_sched, "Scheduler")

        # TAB 6: STATISTIKEN (Gmail)
        t_stats = QWidget(); l_stats = QVBoxLayout(t_stats)
        h_stats_top = QHBoxLayout()
        h_stats_top.addWidget(QLabel("Gmail-Account wählen:"))
        self.cb_gmail_stats = QComboBox()
        h_stats_top.addWidget(self.cb_gmail_stats)
        b_load_stats = QPushButton("Statistiken laden")
        b_load_stats.clicked.connect(self._on_load_stats)
        h_stats_top.addWidget(b_load_stats)
        h_stats_top.addStretch()
        l_stats.addLayout(h_stats_top)

        stats_grp = QGroupBox("Speicher")
        stats_fl = QFormLayout(stats_grp)
        self.lbl_gmail_msgs = QLabel("-")
        self.lbl_drive_total = QLabel("-")
        self.lbl_drive_used = QLabel("-")
        self.lbl_drive_trash = QLabel("-")
        stats_fl.addRow("Nachrichten gesamt:", self.lbl_gmail_msgs)
        stats_fl.addRow("Drive gesamt:", self.lbl_drive_total)
        stats_fl.addRow("Drive belegt:", self.lbl_drive_used)
        stats_fl.addRow("Drive Papierkorb:", self.lbl_drive_trash)
        l_stats.addWidget(stats_grp)
        l_stats.addStretch()
        tabs.addTab(t_stats, "Statistiken")

        # TAB 7: LABELS (Gmail)
        t_labels = QWidget(); l_labels = QVBoxLayout(t_labels)
        h_labels_top = QHBoxLayout()
        h_labels_top.addWidget(QLabel("Gmail-Account wählen:"))
        self.cb_gmail_labels = QComboBox()
        h_labels_top.addWidget(self.cb_gmail_labels)
        b_load_labels = QPushButton("Labels laden")
        b_load_labels.clicked.connect(self._on_load_labels)
        h_labels_top.addWidget(b_load_labels)
        b_create_label = QPushButton("Label erstellen")
        b_create_label.clicked.connect(self._on_create_label)
        h_labels_top.addWidget(b_create_label)
        h_labels_top.addStretch()
        l_labels.addLayout(h_labels_top)

        self.table_labels = QTableWidget(0, 3)
        self.table_labels.setHorizontalHeaderLabels(["Name", "Typ", "Aktionen"])
        self.table_labels.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_labels.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        l_labels.addWidget(self.table_labels)
        tabs.addTab(t_labels, "Labels")

        # TAB 8: LOG
        t4 = QWidget(); l4 = QVBoxLayout(t4)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True)
        l4.addWidget(self.log)
        tabs.addTab(t4, "Log")

        lay.addWidget(tabs)
        self.status = QLabel("Ready"); lay.addWidget(self.status)

        self.refresh_ui()
        self._apply_settings_to_ui()

    def refresh_ui(self):
        """Refreshes all UI elements from the current data model."""
        # Accounts
        self.list_acc.setRowCount(0)
        self.cb_scan_acc.clear(); self.cb_scan_acc.addItem("Alle")
        self.cb_gmail_stats.clear()
        self.cb_gmail_labels.clear()
        for r, a in enumerate(self.accounts):
            self.list_acc.insertRow(r)
            self.list_acc.setItem(r, 0, QTableWidgetItem(a.name))
            proto = getattr(a, "protocol", "IMAP")
            self.list_acc.setItem(r, 1, QTableWidgetItem(f"{a.host} [{proto}]" if a.host else f"[{proto}]"))
            self.list_acc.setItem(r, 2, QTableWidgetItem(a.user))
            self.cb_scan_acc.addItem(a.name)
            if proto != "IMAP":
                self.cb_gmail_stats.addItem(a.name)
                self.cb_gmail_labels.addItem(a.name)

        # Rules
        self.tree_rules.clear()
        for r in self.rules:
            item = QTreeWidgetItem(self.tree_rules)
            item.setText(0, r.name); item.setText(1, r.target_account)
            item.setText(2, r.filter_type); item.setText(3, r.value)
            item.setText(4, "✅" if r.active else "❌")
            item.setData(0, Qt.ItemDataRole.UserRole, r)

    def add_acc(self):
        """Opens the AccountDialog and adds a new account on confirmation."""
        d = AccountDialog(parent=self)
        if d.exec():
            acc, pwd = d.get_account()
            self.accounts.append(acc)
            if KEYRING_AVAIL and pwd:
                try:
                    keyring.set_password(APP_NAME, acc.name, pwd)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Keyring save failed for %s: %s", acc.name, exc)
            self.save_config()
            self.refresh_ui()

    def del_acc(self):
        """Removes the currently selected account."""
        r = self.list_acc.currentRow()
        if r >= 0:
            self.accounts.pop(r)
            self.save_config(); self.refresh_ui()

    def rules_ctx(self, pos):
        """Shows the context menu for the rules tree.

        Args:
            pos: Mouse position for the context menu.
        """
        item = self.tree_rules.itemAt(pos)
        menu = QMenu()
        if item:
            rule = item.data(0, Qt.ItemDataRole.UserRole)
            act_del = menu.addAction("Delete")
        else:
            act_new = menu.addAction("New Rule")

        action = menu.exec(self.tree_rules.mapToGlobal(pos))

        if action and item:
            if action.text() == "Delete":
                self.rules.remove(rule)
                self.save_config()
                self.refresh_ui()
        elif action and not item:
            if action.text() == "New Rule":
                self.add_rule()

    def add_rule(self):
        """Opens the RuleDialog and adds a new rule on confirmation."""
        d = RuleDialog(accounts=self.accounts, parent=self)
        if d.exec(): self.rules.append(d.get_rule()); self.save_config(); self.refresh_ui()

    def run_worker(self, mode, params):
        """Starts a Worker thread for the given mode and parameters.

        Args:
            mode: Worker mode ("rules", "scan_large", or "delete").
            params: Parameter dict for the worker.
        """
        if hasattr(self, "worker") and self.worker and self.worker.isRunning():
            try:
                self.worker.data_ready.disconnect(self.fill_large)
            except (RuntimeError, TypeError):
                pass
            self.worker.requestInterruption()
            self.worker.wait(2000)
        self.worker = Worker(mode, params, self.accounts)
        self.worker.log.connect(self.log.appendPlainText)
        if mode == "scan_large": self.worker.data_ready.connect(self.fill_large)
        self.worker.finished.connect(lambda x: self.status.setText(x))
        self.worker.start()

    def select_rule_folders(self):
        """Opens the FolderSelectDialog and stores the selected folders."""
        if not self.accounts:
            QMessageBox.warning(self, "No Accounts", "Please add an account first.")
            return
        imap_accounts = [a for a in self.accounts if getattr(a, "protocol", "IMAP") == "IMAP"]
        if not imap_accounts:
            QMessageBox.information(
                self,
                "Keine IMAP-Konten",
                "Die Ordnerauswahl gilt nur für IMAP-Konten. Gmail API-Regeln verwenden keine IMAP-Ordner.",
            )
            return
        d = FolderSelectDialog(imap_accounts, parent=self)
        if d.exec():
            self.selected_rule_folders = d.get_selected_folders() or ["INBOX"]
            self.save_config()
            self.status.setText(f"Folders: {', '.join(self.selected_rule_folders)}")

    def run_all_rules(self):
        """Runs all active cleanup rules on the selected folders."""
        self.run_worker("rules", {
            "rules": self.rules,
            "safe_mode": self.settings["safe_mode"],
            "folders": self.selected_rule_folders,
        })

    def run_selected_rules(self):
        """Runs only the selected cleanup rules on the selected folders."""
        sel = [i.data(0, Qt.ItemDataRole.UserRole) for i in self.tree_rules.selectedItems()]
        if sel:
            self.run_worker("rules", {
                "rules": sel,
                "safe_mode": self.settings["safe_mode"],
                "folders": self.selected_rule_folders,
            })

    def start_large_scan(self):
        """Starts a scan for large Gmail/Drive items or IMAP emails."""
        if not self.chk_scan_mail.isChecked() and not self.chk_scan_drive.isChecked():
            QMessageBox.information(
                self,
                "Keine Quelle",
                "Bitte mindestens E-Mails oder Drive-Dateien für den Scan auswählen.",
            )
            return

        self.table_large.setRowCount(0); self.status.setText("Scanning...")
        self.run_worker(
            "scan_large",
            {
                "threshold": self.spin_mb.value(),
                "target_account": self.cb_scan_acc.currentText(),
                "scan_mail": self.chk_scan_mail.isChecked(),
                "scan_drive": self.chk_scan_drive.isChecked(),
            },
        )

    def fill_large(self, items):
        """Populates the large-items table with scan results.

        Args:
            items: List of dicts with account, id, subject/file name, size, and date.
        """
        for row, item in enumerate(items):
            r = self.table_large.rowCount(); self.table_large.insertRow(r)
            chk = QTableWidgetItem(); chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled); chk.setCheckState(Qt.CheckState.Unchecked)
            self.table_large.setItem(r, 0, chk)
            self.table_large.setItem(r, 1, QTableWidgetItem(item['account']))
            self.table_large.setItem(r, 2, QTableWidgetItem(item['subject']))
            self.table_large.setItem(r, 3, QTableWidgetItem(f"{item['size']:.1f}"))
            self.table_large.setItem(r, 4, QTableWidgetItem(item['date']))
            self.table_large.item(r, 0).setData(Qt.ItemDataRole.UserRole, item)
        self.status.setText("Scan complete.")

    def delete_selected(self):
        """Moves checked items to trash (safe mode on) or permanently deletes them.

        After a successful delete action the items are added to the undo history
        so they can be restored from the trash via undo_last_action().
        """
        to_del = []
        for r in range(self.table_large.rowCount()):
            if self.table_large.item(r, 0).checkState() == Qt.CheckState.Checked:
                to_del.append(self.table_large.item(r, 0).data(Qt.ItemDataRole.UserRole))
        if to_del:
            if QMessageBox.question(self, "Delete", f"Delete {len(to_del)} item(s)?") == QMessageBox.StandardButton.Yes:
                safe = self.settings["safe_mode"]
                self.run_worker("delete", {"items": to_del, "safe_mode": safe})
                if safe:
                    # Undo ist nur im Safe Mode (Trash) möglich
                    self._undo_history.append({"items": to_del, "timestamp": datetime.now().isoformat()})
                    self.b_undo.setEnabled(True)
                    self.b_undo.setText(f"↩️ Rückgängig ({len(to_del)} Elemente)")

    def undo_last_action(self):
        """Restores items from the last delete action from the trash."""
        if not self._undo_history:
            QMessageBox.information(self, "Undo", "Keine rückgängig zu machende Aktion vorhanden.")
            return
        last = self._undo_history.pop()
        items = last["items"]
        if QMessageBox.question(
            self, "Undo",
            f"Letzte Aktion rückgängig machen?\n{len(items)} Element(e) aus dem Papierkorb wiederherstellen."
        ) == QMessageBox.StandardButton.Yes:
            self.run_worker("undo", {"items": items, "safe_mode": True})
        else:
            # Aktion wieder in History legen wenn abgebrochen
            self._undo_history.append(last)
        if not self._undo_history:
            self.b_undo.setEnabled(False)
            self.b_undo.setText("↩️ Letzte Aktion rückgängig")

    def update_mode_label(self):
        """Updates the mode indicator label in the header."""
        txt = "🛡️ Trash (Safe)" if self.settings["safe_mode"] else "⚠️ Permanent Delete"
        col = "#4CAF50" if self.settings["safe_mode"] else "#F44336"
        self.lbl_mode.setText(txt); self.lbl_mode.setStyleSheet(f"color: {col}; font-weight: bold; border: 1px solid {col}; padding: 4px;")

    def add_gmail_acc(self):
        """Opens the GmailAccountDialog and adds a new Gmail API account."""
        d = GmailAccountDialog(parent=self)
        if d.exec():
            acc = d.get_account()
            if not acc.name:
                QMessageBox.warning(self, "Fehler", "Bitte einen Namen angeben.")
                return
            self.accounts.append(acc)
            self.save_config()
            self.refresh_ui()

    def export_profile(self):
        """Export the current profile as a secrets-free JSON bundle."""
        default_name = (
            f"universalmailcleaner-profile-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Profil exportieren",
            str(Path.home() / "Downloads" / default_name),
            "JSON-Dateien (*.json)",
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            self._sync_settings_from_ui()
            payload = write_profile(path, self.accounts, self.rules, self.settings)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export fehlgeschlagen",
                f"Das Profil konnte nicht exportiert werden:\n{exc}",
            )
            return
        self.log.appendPlainText(
            f"[Profil] Exportiert: {path} ({len(payload['accounts'])} Konten, {len(payload['rules'])} Regeln)"
        )
        self.status.setText("Profil exportiert.")

    def import_profile(self):
        """Import a previously exported secrets-free profile JSON."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Profil importieren",
            str(Path.home() / "Downloads"),
            "JSON-Dateien (*.json)",
        )
        if not path:
            return
        try:
            accounts, rules, settings = read_profile(path)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Import fehlgeschlagen",
                f"Das Profil konnte nicht importiert werden:\n{exc}",
            )
            return

        existing_accounts = len(self.accounts)
        existing_rules = len(self.rules)
        if existing_accounts or existing_rules:
            answer = QMessageBox.question(
                self,
                "Profil importieren",
                (
                    "Der Import ersetzt die aktuelle Profilkonfiguration.\n\n"
                    f"Aktuell: {existing_accounts} Konten, {existing_rules} Regeln\n"
                    f"Import: {len(accounts)} Konten, {len(rules)} Regeln\n\n"
                    "Passwörter und OAuth-Zugänge werden nicht importiert und "
                    "müssen bei Bedarf lokal neu gesetzt werden.\n\n"
                    "Fortfahren?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.accounts = accounts
        self.rules = rules
        self.settings = merge_profile_settings(settings)
        self.selected_rule_folders = list(
            self.settings.get("selected_rule_folders", ["INBOX"])
        )
        self.refresh_ui()
        self._apply_settings_to_ui()
        self.save_config()
        self.log.appendPlainText(
            f"[Profil] Importiert: {path} ({len(self.accounts)} Konten, {len(self.rules)} Regeln)"
        )
        self.status.setText("Profil importiert.")

    # ------------------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------------------

    def _on_scheduler_run(self):
        """Triggered by the scheduler timer or manual 'Jetzt ausführen' click."""
        self.log.appendPlainText(f"[Scheduler] Automatischer Lauf gestartet ({datetime.now().strftime('%H:%M:%S')})")
        self.run_all_rules()
        # Persist updated last_run / next_run in settings
        self.settings["scheduler"] = self._scheduler.get_config().to_dict()
        self.save_config()

    # ------------------------------------------------------------------
    # Gmail Statistics tab
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_bytes(n: int) -> str:
        """Format a byte count as a human-readable string (KB/MB/GB)."""
        if n < 0:
            return "-"
        if n < 1024:
            return f"{n} B"
        if n < 1024 ** 2:
            return f"{n / 1024:.1f} KB"
        if n < 1024 ** 3:
            return f"{n / 1024 ** 2:.1f} MB"
        return f"{n / 1024 ** 3:.2f} GB"

    def _get_gmail_service_for(self, account_name: str):
        """Return an authenticated GmailService for the named Gmail API account.

        The import is deferred so the google libraries are only required
        when actually used.

        Returns:
            Authenticated GmailService, or None on failure.
        """
        acc = next((a for a in self.accounts if a.name == account_name), None)
        if acc is None or getattr(acc, "protocol", "IMAP") != "Gmail API":
            QMessageBox.warning(self, "Kein Gmail-Account", f"Account '{account_name}' ist kein Gmail API-Account.")
            return None
        try:
            from gmail_service import GmailService
        except ImportError as exc:
            QMessageBox.critical(self, "Import-Fehler", f"gmail_service konnte nicht importiert werden:\n{exc}")
            return None
        svc = GmailService()
        if not svc.auth():
            QMessageBox.critical(self, "Auth fehlgeschlagen", "Gmail OAuth2-Login fehlgeschlagen.\nSiehe Log für Details.")
            return None
        return svc

    def _on_load_stats(self):
        """Load Gmail/Drive storage statistics in a background thread."""
        account_name = self.cb_gmail_stats.currentText()
        if not account_name:
            QMessageBox.information(self, "Kein Account", "Kein Gmail API-Account vorhanden.")
            return

        self.status.setText("Lade Statistiken...")
        self.lbl_gmail_msgs.setText("...")
        self.lbl_drive_total.setText("...")
        self.lbl_drive_used.setText("...")
        self.lbl_drive_trash.setText("...")

        svc = self._get_gmail_service_for(account_name)
        if svc is None:
            self.status.setText("Statistiken: Fehler")
            return

        class StatsWorker(QThread):
            done = Signal(dict)
            error = Signal(str)

            def __init__(self, service):
                super().__init__()
                self._svc = service

            def run(self):
                try:
                    self.done.emit(self._svc.get_storage_stats())
                except Exception as exc:
                    self.error.emit(str(exc))

        self._stats_worker = StatsWorker(svc)

        def _on_done(stats):
            self.lbl_gmail_msgs.setText(str(stats.get("gmail_used", 0)))
            self.lbl_drive_total.setText(self._fmt_bytes(stats.get("drive_total", 0)))
            self.lbl_drive_used.setText(self._fmt_bytes(stats.get("drive_used", 0)))
            self.lbl_drive_trash.setText(self._fmt_bytes(stats.get("drive_trash", 0)))
            self.status.setText("Statistiken geladen.")

        def _on_error(msg):
            self.status.setText("Statistiken: Fehler")
            self.log.appendPlainText(f"[Statistiken] Fehler: {msg}")

        self._stats_worker.done.connect(_on_done)
        self._stats_worker.error.connect(_on_error)
        self._stats_worker.start()

    # ------------------------------------------------------------------
    # Gmail Labels tab
    # ------------------------------------------------------------------

    def _on_load_labels(self):
        """Load Gmail labels in a background thread and populate the table."""
        account_name = self.cb_gmail_labels.currentText()
        if not account_name:
            QMessageBox.information(self, "Kein Account", "Kein Gmail API-Account vorhanden.")
            return

        self.status.setText("Lade Labels...")
        self.table_labels.setRowCount(0)

        svc = self._get_gmail_service_for(account_name)
        if svc is None:
            self.status.setText("Labels: Fehler")
            return

        class LabelsWorker(QThread):
            done = Signal(list)
            error = Signal(str)

            def __init__(self, service):
                super().__init__()
                self._svc = service

            def run(self):
                try:
                    self.done.emit(self._svc.get_labels())
                except Exception as exc:
                    self.error.emit(str(exc))

        self._labels_worker = LabelsWorker(svc)
        self._labels_svc = svc
        self._labels_account_name = account_name

        def _on_done(labels):
            self._populate_labels_table(labels)
            self.status.setText(f"{len(labels)} Labels geladen.")

        def _on_error(msg):
            self.status.setText("Labels: Fehler")
            self.log.appendPlainText(f"[Labels] Fehler: {msg}")

        self._labels_worker.done.connect(_on_done)
        self._labels_worker.error.connect(_on_error)
        self._labels_worker.start()

    def _populate_labels_table(self, labels):
        """Render the labels table for the Gmail labels tab."""
        self.table_labels.setRowCount(0)
        for label in labels:
            row = self.table_labels.rowCount()
            self.table_labels.insertRow(row)
            self.table_labels.setItem(row, 0, QTableWidgetItem(label.get("name", "")))
            ltype = label.get("type", "user")
            self.table_labels.setItem(row, 1, QTableWidgetItem(ltype))
            actions_widget = self._build_label_actions(label)
            if actions_widget is not None:
                self.table_labels.setCellWidget(row, 2, actions_widget)

    def _build_label_actions(self, label):
        """Create the action buttons for one label row."""
        if label.get("type", "user") != "user":
            return None

        label_id = label.get("id", "")
        label_name = label.get("name", label_id)

        actions = QWidget(self.table_labels)
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        b_clear = QPushButton("Leeren")
        b_clear.setToolTip("Alle Mails mit diesem Label in den Papierkorb verschieben.")
        b_clear.clicked.connect(lambda: self._delete_by_label(label_id, label_name))
        layout.addWidget(b_clear)

        b_rename = QPushButton("Umbenennen")
        b_rename.clicked.connect(lambda: self._rename_label(label_id, label_name))
        layout.addWidget(b_rename)

        b_delete = QPushButton("Löschen")
        b_delete.setToolTip("Nur das Label löschen, nicht die enthaltenen Mails.")
        b_delete.clicked.connect(lambda: self._delete_label_definition(label_id, label_name))
        layout.addWidget(b_delete)

        return actions

    def _ensure_labels_service(self):
        """Return an authenticated GmailService for the selected labels account."""
        account_name = self.cb_gmail_labels.currentText()
        if not account_name:
            QMessageBox.information(self, "Kein Account", "Kein Gmail API-Account vorhanden.")
            return None

        svc = getattr(self, "_labels_svc", None)
        if svc is not None and getattr(self, "_labels_account_name", None) == account_name:
            return svc

        svc = self._get_gmail_service_for(account_name)
        if svc is None:
            return None

        self._labels_svc = svc
        self._labels_account_name = account_name
        return svc

    def _run_label_service_task(self, action, on_done, error_prefix):
        """Run a Gmail label action in the background."""
        class LabelActionWorker(QThread):
            done = Signal(object)
            error = Signal(str)

            def __init__(self, task):
                super().__init__()
                self._task = task

            def run(self):
                try:
                    self.done.emit(self._task())
                except Exception as exc:
                    self.error.emit(str(exc))

        if not hasattr(self, "_label_action_workers"):
            self._label_action_workers: list = []

        worker = LabelActionWorker(action)
        self._label_action_workers.append(worker)

        def _on_error(msg):
            self.log.appendPlainText(f"[Labels] {error_prefix}: {msg}")
            self.status.setText("Labels: Fehler")

        def _cleanup(_w=worker):
            if _w in self._label_action_workers:
                self._label_action_workers.remove(_w)

        worker.done.connect(on_done)
        worker.error.connect(_on_error)
        worker.finished.connect(_cleanup)
        worker.start()

    def _prompt_label_name(self, title: str, prompt: str, initial: str = "") -> Optional[str]:
        """Prompt the user for a label name and return a trimmed value."""
        text, ok = QInputDialog.getText(self, title, prompt, text=initial)
        if not ok:
            return None

        label_name = text.strip()
        if not label_name:
            QMessageBox.information(self, title, "Bitte einen Label-Namen eingeben.")
            return None
        return label_name

    def _on_create_label(self):
        """Create a new Gmail user label for the selected account."""
        svc = self._ensure_labels_service()
        if svc is None:
            return

        label_name = self._prompt_label_name("Label erstellen", "Name des neuen Labels:")
        if label_name is None:
            return

        self.status.setText("Erstelle Label...")

        def _on_done(label):
            created_name = label.get("name", label_name)
            self.log.appendPlainText(f"[Labels] Label '{created_name}' erstellt.")
            self.status.setText(f"Label '{created_name}' erstellt.")
            self._on_load_labels()

        self._run_label_service_task(
            lambda: svc.create_label(label_name),
            _on_done,
            "Fehler beim Erstellen",
        )

    def _rename_label(self, label_id: str, current_name: str):
        """Rename an existing Gmail user label."""
        svc = self._ensure_labels_service()
        if svc is None:
            return

        new_name = self._prompt_label_name(
            "Label umbenennen",
            "Neuer Name für das Label:",
            current_name,
        )
        if new_name is None or new_name == current_name:
            return

        self.status.setText("Benenne Label um...")

        def _on_done(label):
            updated_name = label.get("name", new_name)
            self.log.appendPlainText(
                f"[Labels] Label '{current_name}' in '{updated_name}' umbenannt."
            )
            self.status.setText(f"Label '{updated_name}' umbenannt.")
            self._on_load_labels()

        self._run_label_service_task(
            lambda: svc.rename_label(label_id, new_name),
            _on_done,
            "Fehler beim Umbenennen",
        )

    def _delete_label_definition(self, label_id: str, label_name: str):
        """Delete a Gmail user label without deleting the contained mails."""
        reply = QMessageBox.question(
            self,
            "Label löschen",
            (
                f"Label '{label_name}' löschen?\n"
                "Das Label wird von den verknüpften Mails entfernt, "
                "die Mails selbst bleiben erhalten."
            ),
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        svc = self._ensure_labels_service()
        if svc is None:
            return

        self.status.setText("Lösche Label...")

        def _on_done(_result):
            self.log.appendPlainText(f"[Labels] Label '{label_name}' gelöscht.")
            self.status.setText(f"Label '{label_name}' gelöscht.")
            self._on_load_labels()

        self._run_label_service_task(
            lambda: svc.delete_label(label_id),
            _on_done,
            "Fehler beim Löschen",
        )

    def _delete_by_label(self, label_id: str, label_name: str):
        """Move all messages with the given label to Trash (background thread)."""
        reply = QMessageBox.question(
            self,
            "Label leeren",
            f"Alle Mails mit Label '{label_name}' in den Papierkorb verschieben?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        svc = getattr(self, "_labels_svc", None)
        if svc is None:
            self.log.appendPlainText("[Labels] Kein aktiver Gmail-Service. Bitte zuerst Labels laden.")
            return

        class DeleteLabelWorker(QThread):
            done = Signal(int)
            error = Signal(str)

            def __init__(self, service, lid):
                super().__init__()
                self._svc = service
                self._lid = lid

            def run(self):
                try:
                    self.done.emit(self._svc.delete_by_label(self._lid, trash=True))
                except Exception as exc:
                    self.error.emit(str(exc))

        self._del_label_worker = DeleteLabelWorker(svc, label_id)

        def _on_done(count):
            self.log.appendPlainText(f"[Labels] {count} Mail(s) von Label '{label_name}' in Papierkorb verschoben.")
            self.status.setText(f"Label '{label_name}': {count} Mails gelöscht.")

        def _on_error(msg):
            self.log.appendPlainText(f"[Labels] Fehler beim Löschen: {msg}")
            self.status.setText("Labels: Fehler")

        self._del_label_worker.done.connect(_on_done)
        self._del_label_worker.error.connect(_on_error)
        self._del_label_worker.start()

    def closeEvent(self, event):
        """Persist scheduler config and stop running workers on application close."""
        if hasattr(self, "worker") and self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(3000)
        for attr in ("_stats_worker", "_labels_worker", "_del_label_worker"):
            w = getattr(self, attr, None)
            if w is not None and w.isRunning():
                w.requestInterruption()
                w.wait(2000)
        for w in getattr(self, "_label_action_workers", []):
            if w.isRunning():
                w.requestInterruption()
                w.wait(2000)
        self.save_config()
        super().closeEvent(event)

    def save_settings_ui(self, *_args):
        """Saves settings when the safe mode checkbox is toggled."""
        self.save_config()
        self.update_mode_label()

def main() -> int:
    """Start the desktop application."""
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
