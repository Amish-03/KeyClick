"""
action_executor.py — Mouse click simulation and window detection.

Handles moving the cursor, performing clicks, and checking whether
the target application window is in the foreground.
"""

from pynput.mouse import Button, Controller as MouseController

try:
    import win32gui  # type: ignore
    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False


# Module-level mouse controller (thread-safe for pynput)
_mouse = MouseController()


def execute_click(x: int, y: int, restore_position: bool = True) -> None:
    """
    Move the cursor to (x, y), perform a left click, and optionally
    restore the cursor to its original position.
    """
    original = _mouse.position  # save current position

    _mouse.position = (x, y)
    _mouse.click(Button.left)

    if restore_position:
        _mouse.position = original


def is_target_window_foreground(window_title: str) -> bool:
    """
    Check whether the foreground window's title contains *window_title*
    (case-insensitive substring match).

    Returns True if win32gui is unavailable (fail-open) so the app
    still works even without pywin32.
    """
    if not _HAS_WIN32:
        return True  # fail-open

    try:
        hwnd = win32gui.GetForegroundWindow()
        fg_title = win32gui.GetWindowText(hwnd)
        return window_title.lower() in fg_title.lower()
    except Exception:
        return True  # fail-open on errors
