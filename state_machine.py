"""
state_machine.py — Application state management.

Defines the possible application states and manages transitions
between them with validation and Qt signal emission.
"""

from enum import Enum, auto
from PyQt6.QtCore import QObject, pyqtSignal


class AppState(Enum):
    """Possible application states."""
    NORMAL = auto()            # Listening for mapped keys, executing clicks
    CONFIG_WAIT_KEY = auto()   # Waiting for user to press a key to configure
    CONFIG_WAIT_CLICK = auto() # Waiting for user to click the target position
    DISABLED = auto()          # System paused — no key actions


# Human-readable labels for the UI
STATE_LABELS = {
    AppState.NORMAL: "NORMAL",
    AppState.CONFIG_WAIT_KEY: "CONFIG — Press a key…",
    AppState.CONFIG_WAIT_CLICK: "CONFIG — Click target…",
    AppState.DISABLED: "DISABLED",
}

# Allowed transitions: state → set of valid next states
VALID_TRANSITIONS = {
    AppState.NORMAL: {AppState.CONFIG_WAIT_KEY, AppState.DISABLED},
    AppState.CONFIG_WAIT_KEY: {AppState.CONFIG_WAIT_CLICK, AppState.NORMAL},
    AppState.CONFIG_WAIT_CLICK: {AppState.NORMAL},
    AppState.DISABLED: {AppState.NORMAL},
}


class StateMachine(QObject):
    """
    Manages application state with validated transitions.

    Signals:
        state_changed(AppState): emitted whenever the state changes.
    """

    state_changed = pyqtSignal(object)  # AppState

    def __init__(self, initial_state: AppState = AppState.NORMAL):
        super().__init__()
        self._state = initial_state

    @property
    def state(self) -> AppState:
        return self._state

    def transition(self, new_state: AppState) -> bool:
        """
        Attempt a state transition.

        Returns True if the transition was valid and executed,
        False if the transition is not allowed.
        """
        if new_state == self._state:
            return True  # no-op

        allowed = VALID_TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            return False

        self._state = new_state
        self.state_changed.emit(self._state)
        return True

    def is_normal(self) -> bool:
        return self._state == AppState.NORMAL

    def is_config(self) -> bool:
        return self._state in (AppState.CONFIG_WAIT_KEY, AppState.CONFIG_WAIT_CLICK)

    def is_disabled(self) -> bool:
        return self._state == AppState.DISABLED
