"""
input_listener.py — Global keyboard and mouse input capture.

Provides threaded listeners for keyboard key presses and single mouse-click
capture using pynput, bridged to the Qt event loop via signals.
"""

import threading
from pynput import keyboard, mouse
from PyQt6.QtCore import QObject, pyqtSignal


def normalise_key(key) -> str:
    """
    Convert a pynput key object to a consistent lowercase string.

    Examples:
        Key.f1     → "f1"
        Key.space  → "space"
        Key.ctrl_l → "ctrl_l"
        KeyCode 'a' → "a"
    """
    if isinstance(key, keyboard.Key):
        return key.name.lower()  # e.g. "f1", "space", "ctrl_l"
    elif isinstance(key, keyboard.KeyCode):
        if key.char is not None:
            return key.char.lower()
        # Virtual key with no char (rare)
        if key.vk is not None:
            return f"vk_{key.vk}"
    return str(key).lower()


class KeyboardListener(QObject):
    """
    Wraps pynput.keyboard.Listener to emit Qt signals for each key press.

    The listener runs in a daemon thread so it doesn't block the UI.

    Signals:
        key_pressed(str): emitted with the normalised key name on key-down.
    """

    key_pressed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._listener: keyboard.Listener | None = None
        self._running = False

    def start(self) -> None:
        """Start listening for keyboard events."""
        if self._running:
            return
        self._running = True
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Stop the keyboard listener."""
        self._running = False
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key) -> None:
        """Callback invoked by pynput in the listener thread."""
        if not self._running:
            return
        name = normalise_key(key)
        self.key_pressed.emit(name)


class MouseClickCapture(QObject):
    """
    Captures a single mouse click position and then auto-stops.

    Signals:
        mouse_clicked(int, int): emitted with (x, y) screen coordinates
                                  when the user clicks.
    """

    mouse_clicked = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self._listener: mouse.Listener | None = None
        self._active = False

    def start(self) -> None:
        """Start listening for one mouse click."""
        if self._active:
            return
        self._active = True
        self._listener = mouse.Listener(on_click=self._on_click)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Cancel capture if still running."""
        self._active = False
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_click(self, x: int, y: int, button, pressed: bool):
        """
        Called by pynput on any mouse button event.

        We only care about the left-button *press* (not release).
        After capturing, we stop the listener automatically.
        """
        if not self._active:
            return False  # stop listener

        if button == mouse.Button.left and pressed:
            self._active = False
            self.mouse_clicked.emit(int(x), int(y))
            return False  # stop listener after capture
