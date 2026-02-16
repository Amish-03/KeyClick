"""
mapping_manager.py — Orchestrates key-to-coordinate mappings.

Thin layer between ConfigManager and the rest of the application,
providing a signal-driven API for mapping mutations.
"""

from typing import Dict, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
from config_manager import ConfigManager


class MappingManager(QObject):
    """
    Manages key→(x, y) mappings with change notifications.

    Signals:
        mappings_changed(): emitted after any add/remove operation.
    """

    mappings_changed = pyqtSignal()

    def __init__(self, config: ConfigManager):
        super().__init__()
        self._config = config

    def add_mapping(self, key: str, x: int, y: int) -> None:
        """Add or overwrite a mapping and notify listeners."""
        self._config.set_mapping(key, x, y)
        self.mappings_changed.emit()

    def remove_mapping(self, key: str) -> bool:
        """Remove a mapping by key. Returns True if it existed."""
        removed = self._config.remove_mapping(key)
        if removed:
            self.mappings_changed.emit()
        return removed

    def get_all_mappings(self) -> Dict[str, Dict[str, int]]:
        """Return all mappings as {key: {"x": ..., "y": ...}}."""
        return self._config.get_mappings()

    def get_mapping(self, key: str) -> Optional[Tuple[int, int]]:
        """Return (x, y) for *key*, or None."""
        return self._config.get_mapping(key)
