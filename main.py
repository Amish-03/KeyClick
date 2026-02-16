"""
main.py — KeyClick application entry point and controller.

Wires together all modules: UI, state machine, input listeners,
mapping manager, action executor, and configuration.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from config_manager import ConfigManager
from state_machine import StateMachine, AppState
from input_listener import KeyboardListener, MouseClickCapture
from action_executor import execute_click, is_target_window_foreground
from mapping_manager import MappingManager
from ui import MainWindow


class AppController:
    """
    Central coordinator that connects all application components.

    Responsibilities:
      • React to UI signals (add, remove, toggle, settings)
      • Drive the configuration flow (state machine transitions)
      • Dispatch key-press events to the action executor
    """

    def __init__(self):
        # ── Core components ──
        self.config = ConfigManager()
        self.state_machine = StateMachine(AppState.NORMAL)
        self.mapping_manager = MappingManager(self.config)
        self.keyboard_listener = KeyboardListener()
        self.mouse_capture = MouseClickCapture()

        # ── UI ──
        self.window = MainWindow()

        # ── Temp state for configuration flow ──
        self._pending_key: str | None = None

        self._wire_signals()
        self._initialize_ui()

        # Start keyboard listener
        self.keyboard_listener.start()

    # ──────────────────────────────────────────────────────────────────
    # Signal wiring
    # ──────────────────────────────────────────────────────────────────

    def _wire_signals(self) -> None:
        # State machine → UI
        self.state_machine.state_changed.connect(self._on_state_changed)

        # Mapping changes → refresh table
        self.mapping_manager.mappings_changed.connect(self._refresh_table)

        # UI buttons
        self.window.add_key_requested.connect(self._on_add_key)
        self.window.remove_key_requested.connect(self._on_remove_key)
        self.window.toggle_system_requested.connect(self._on_toggle_system)
        self.window.setting_changed.connect(self._on_setting_changed)
        self.window.quit_requested.connect(self._on_quit)

        # Input listeners
        self.keyboard_listener.key_pressed.connect(self._on_key_pressed)
        self.mouse_capture.mouse_clicked.connect(self._on_mouse_clicked)

    def _initialize_ui(self) -> None:
        """Load persisted state into the UI."""
        settings = self.config.get_settings()
        self.window.set_settings_ui(
            restore=settings.get("restore_mouse_position", True),
            foreground=settings.get("require_foreground_window", False),
        )
        self._refresh_table()
        self.window.set_status("Ready — press a mapped key or add a new mapping.")

    # ──────────────────────────────────────────────────────────────────
    # State machine reactions
    # ──────────────────────────────────────────────────────────────────

    def _on_state_changed(self, new_state: AppState) -> None:
        self.window.update_state(new_state)

    # ──────────────────────────────────────────────────────────────────
    # Key press handling (NORMAL mode + CONFIG flow)
    # ──────────────────────────────────────────────────────────────────

    def _on_key_pressed(self, key_name: str) -> None:
        state = self.state_machine.state

        if state == AppState.CONFIG_WAIT_KEY:
            # ── Config Step 1: capture the key ──
            self._pending_key = key_name
            self.state_machine.transition(AppState.CONFIG_WAIT_CLICK)
            self.window.set_status(
                f'Key "{key_name}" captured.  Now click on the target screen position.'
            )
            # Start one-shot mouse capture
            self.mouse_capture.start()
            return

        if state == AppState.NORMAL:
            # ── Normal mode: execute mapped click ──
            mapping = self.mapping_manager.get_mapping(key_name)
            if mapping is None:
                return  # unmapped key — ignore

            x, y = mapping

            # Foreground check
            if self.config.get_setting("require_foreground_window", False):
                title = self.config.get_setting("target_window_title", "Valeton")
                if not is_target_window_foreground(title):
                    return  # target window not in focus

            restore = self.config.get_setting("restore_mouse_position", True)
            execute_click(x, y, restore_position=restore)
            self.window.set_status(f'Executed click at ({x}, {y}) for key "{key_name}".')

    # ──────────────────────────────────────────────────────────────────
    # Mouse click capture (CONFIG flow step 2)
    # ──────────────────────────────────────────────────────────────────

    def _on_mouse_clicked(self, x: int, y: int) -> None:
        if self.state_machine.state != AppState.CONFIG_WAIT_CLICK:
            return

        key = self._pending_key
        self._pending_key = None

        if key is not None:
            self.mapping_manager.add_mapping(key, x, y)
            self.window.set_status(f'Mapping saved: "{key}" → ({x}, {y})')

        self.state_machine.transition(AppState.NORMAL)

    # ──────────────────────────────────────────────────────────────────
    # UI button handlers
    # ──────────────────────────────────────────────────────────────────

    def _on_add_key(self) -> None:
        """Start configuration flow (enter CONFIG_WAIT_KEY)."""
        if self.state_machine.state == AppState.DISABLED:
            self.window.set_status("Enable the system before adding keys.")
            return
        if self.state_machine.transition(AppState.CONFIG_WAIT_KEY):
            self.window.set_status("Press the key you want to configure…")

    def _on_remove_key(self) -> None:
        """Remove the currently selected mapping from the table."""
        key = self.window.selected_key()
        if key is None:
            self.window.set_status("Select a mapping to remove first.")
            return
        if self.mapping_manager.remove_mapping(key):
            self.window.set_status(f'Removed mapping for "{key}".')
        else:
            self.window.set_status(f'Key "{key}" not found.')

    def _on_toggle_system(self) -> None:
        """Toggle between NORMAL and DISABLED."""
        if self.state_machine.is_disabled():
            self.state_machine.transition(AppState.NORMAL)
            self.window.set_status("System enabled.")
        elif self.state_machine.is_normal():
            self.state_machine.transition(AppState.DISABLED)
            self.window.set_status("System disabled — no keys will trigger clicks.")

    def _on_setting_changed(self, key: str, value: object) -> None:
        """Persist a settings toggle from the UI."""
        self.config.update_setting(key, value)
        self.window.set_status(f'Setting "{key}" updated to {value}.')

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        self.window.refresh_mappings(self.mapping_manager.get_all_mappings())

    def _on_quit(self) -> None:
        """Graceful shutdown."""
        self.keyboard_listener.stop()
        self.mouse_capture.stop()
        QApplication.instance().quit()

    def show(self) -> None:
        self.window.show()


# ======================================================================
# Entry point
# ======================================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("KeyClick")
    app.setQuitOnLastWindowClosed(False)  # keep running in tray

    controller = AppController()
    controller.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
