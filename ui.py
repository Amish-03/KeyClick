"""
ui.py — PyQt6 graphical user interface for KeyClick.

Provides the main window with:
  • Mode indicator badge
  • Status message bar
  • Scrollable mapping table
  • Control buttons (Add, Remove, Enable/Disable)
  • Settings checkboxes
  • System-tray icon with context menu
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QSystemTrayIcon, QMenu, QFrame, QApplication,
    QAbstractItemView, QGroupBox,
)

from state_machine import AppState


# ──────────────────────────────────────────────────────────────────────
# Stylesheet (Dark theme with teal accent)
# ──────────────────────────────────────────────────────────────────────

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

QLabel#title {
    font-size: 22px;
    font-weight: bold;
    color: #89b4fa;
    padding: 4px 0;
}

QLabel#statusLabel {
    font-size: 12px;
    color: #a6adc8;
    padding: 6px 10px;
    background-color: #181825;
    border-radius: 6px;
    min-height: 20px;
}

QLabel#modeBadge {
    font-size: 13px;
    font-weight: bold;
    padding: 5px 14px;
    border-radius: 8px;
    min-width: 120px;
    qproperty-alignment: AlignCenter;
}

QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #45475a;
    border-color: #89b4fa;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton#addBtn {
    background-color: #1e6640;
    border-color: #2d9d5f;
}
QPushButton#addBtn:hover {
    background-color: #2d9d5f;
}
QPushButton#removeBtn {
    background-color: #6e2532;
    border-color: #c94f6d;
}
QPushButton#removeBtn:hover {
    background-color: #c94f6d;
}
QPushButton#toggleBtn {
    background-color: #45475a;
    border-color: #89b4fa;
}

QTableWidget {
    background-color: #181825;
    alternate-background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    gridline-color: #313244;
    selection-background-color: #45475a;
    padding: 2px;
}
QTableWidget::item {
    padding: 6px 10px;
}
QHeaderView::section {
    background-color: #313244;
    color: #89b4fa;
    font-weight: bold;
    padding: 6px 10px;
    border: none;
    border-bottom: 2px solid #89b4fa;
}

QCheckBox {
    spacing: 8px;
    color: #cdd6f4;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #45475a;
    border-radius: 4px;
    background-color: #181825;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 18px;
    font-weight: bold;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
"""


# Badge colours per state
_BADGE_STYLES = {
    AppState.NORMAL: "background-color: #1e6640; color: #a6e3a1;",
    AppState.CONFIG_WAIT_KEY: "background-color: #7c5a1e; color: #f9e2af;",
    AppState.CONFIG_WAIT_CLICK: "background-color: #7c5a1e; color: #f9e2af;",
    AppState.DISABLED: "background-color: #6e2532; color: #f38ba8;",
}

_BADGE_TEXT = {
    AppState.NORMAL: "● NORMAL",
    AppState.CONFIG_WAIT_KEY: "◉ CONFIG — Key",
    AppState.CONFIG_WAIT_CLICK: "◉ CONFIG — Click",
    AppState.DISABLED: "■ DISABLED",
}


class MainWindow(QMainWindow):
    """
    Primary application window.

    Signals (outbound to controller):
        add_key_requested()       — user clicked "Add / Configure Key"
        remove_key_requested()    — user clicked "Remove Selected"
        toggle_system_requested() — user clicked Enable / Disable
        setting_changed(str, object) — a setting checkbox toggled
        quit_requested()          — user wants to exit
    """

    add_key_requested = pyqtSignal()
    remove_key_requested = pyqtSignal()
    toggle_system_requested = pyqtSignal()
    setting_changed = pyqtSignal(str, object)
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KeyClick — Keyboard → Mouse Mapper")
        self.setMinimumSize(520, 520)
        self.resize(560, 600)
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._build_tray()
        self._connect_signals()

        self.update_state(AppState.NORMAL)

    # ──────────────────────────────────────────────────────────────────
    # UI Construction
    # ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # ── Header row ──
        header = QHBoxLayout()
        self._title = QLabel("KeyClick")
        self._title.setObjectName("title")
        header.addWidget(self._title)
        header.addStretch()
        self._mode_badge = QLabel()
        self._mode_badge.setObjectName("modeBadge")
        header.addWidget(self._mode_badge)
        root.addLayout(header)

        # ── Status message ──
        self._status = QLabel("Ready")
        self._status.setObjectName("statusLabel")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        # ── Mapping table ──
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Key", "X", "Y"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self._table, stretch=1)

        # ── Button row ──
        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("➕  Add / Configure Key")
        self._add_btn.setObjectName("addBtn")
        self._remove_btn = QPushButton("✕  Remove Selected")
        self._remove_btn.setObjectName("removeBtn")
        self._toggle_btn = QPushButton("⏸  Disable")
        self._toggle_btn.setObjectName("toggleBtn")
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)
        btn_row.addWidget(self._toggle_btn)
        root.addLayout(btn_row)

        # ── Settings ──
        settings_box = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_box)
        self._chk_restore = QCheckBox("Restore mouse position after click")
        self._chk_foreground = QCheckBox("Only execute when target window is foreground")
        settings_layout.addWidget(self._chk_restore)
        settings_layout.addWidget(self._chk_foreground)
        root.addWidget(settings_box)

    def _build_tray(self) -> None:
        """Set up system tray icon and its context menu."""
        self._tray = QSystemTrayIcon(self)
        # Use the default app icon; fallback to a themed icon
        icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_ComputerIcon
        )
        self._tray.setIcon(icon)
        self._tray.setToolTip("KeyClick")

        menu = QMenu()
        show_action = menu.addAction("Show")
        show_action.triggered.connect(self._show_from_tray)
        hide_action = menu.addAction("Hide")
        hide_action.triggered.connect(self.hide)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _connect_signals(self) -> None:
        self._add_btn.clicked.connect(self.add_key_requested.emit)
        self._remove_btn.clicked.connect(self.remove_key_requested.emit)
        self._toggle_btn.clicked.connect(self.toggle_system_requested.emit)
        self._chk_restore.toggled.connect(
            lambda v: self.setting_changed.emit("restore_mouse_position", v)
        )
        self._chk_foreground.toggled.connect(
            lambda v: self.setting_changed.emit("require_foreground_window", v)
        )

    # ──────────────────────────────────────────────────────────────────
    # Public API (called by the controller)
    # ──────────────────────────────────────────────────────────────────

    def update_state(self, state: AppState) -> None:
        """Update the mode badge and button labels to reflect *state*."""
        self._mode_badge.setText(_BADGE_TEXT.get(state, ""))
        self._mode_badge.setStyleSheet(
            _BADGE_STYLES.get(state, "") + " font-size: 13px; font-weight: bold; "
            "padding: 5px 14px; border-radius: 8px; min-width: 120px;"
        )

        is_config = state in (AppState.CONFIG_WAIT_KEY, AppState.CONFIG_WAIT_CLICK)
        self._add_btn.setEnabled(not is_config)
        self._remove_btn.setEnabled(not is_config)

        if state == AppState.DISABLED:
            self._toggle_btn.setText("▶  Enable")
        else:
            self._toggle_btn.setText("⏸  Disable")
        self._toggle_btn.setEnabled(not is_config)

    def set_status(self, text: str) -> None:
        """Update the status message bar."""
        self._status.setText(text)

    def set_settings_ui(self, restore: bool, foreground: bool) -> None:
        """Initialise checkbox states (without emitting signals)."""
        self._chk_restore.blockSignals(True)
        self._chk_foreground.blockSignals(True)
        self._chk_restore.setChecked(restore)
        self._chk_foreground.setChecked(foreground)
        self._chk_restore.blockSignals(False)
        self._chk_foreground.blockSignals(False)

    def refresh_mappings(self, mappings: dict) -> None:
        """Rebuild the mapping table from scratch."""
        self._table.setRowCount(0)
        for key, coords in sorted(mappings.items()):
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(key))
            self._table.setItem(row, 1, QTableWidgetItem(str(coords["x"])))
            self._table.setItem(row, 2, QTableWidgetItem(str(coords["y"])))

    def selected_key(self) -> str | None:
        """Return the key column value of the currently selected row."""
        items = self._table.selectedItems()
        if items:
            row = items[0].row()
            key_item = self._table.item(row, 0)
            if key_item:
                return key_item.text()
        return None

    # ──────────────────────────────────────────────────────────────────
    # Tray helpers
    # ──────────────────────────────────────────────────────────────────

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.activateWindow()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def closeEvent(self, event) -> None:
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "KeyClick",
            "Application minimised to system tray.",
            QSystemTrayIcon.MessageIcon.Information,
            1500,
        )
