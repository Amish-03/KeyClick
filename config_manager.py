"""
config_manager.py — JSON-based configuration persistence.

Handles loading, saving, and mutating the application config file
(config.json) which stores key→coordinate mappings and user settings.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


# Default configuration template
DEFAULT_CONFIG: Dict[str, Any] = {
    "mappings": {},
    "settings": {
        "restore_mouse_position": True,
        "require_foreground_window": False,
        "target_window_title": "Valeton",
    },
}


class ConfigManager:
    """Manages persistent JSON configuration for the application."""

    def __init__(self, config_path: Optional[str] = None):
        # Default to config.json next to this script
        if config_path is None:
            app_dir = Path(__file__).resolve().parent
            self._path = app_dir / "config.json"
        else:
            self._path = Path(config_path)

        self._data: Dict[str, Any] = {}
        self.load()

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load config from disk, or create default if missing/corrupt."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                # Ensure required top-level keys exist
                if "mappings" not in self._data:
                    self._data["mappings"] = {}
                if "settings" not in self._data:
                    self._data["settings"] = dict(DEFAULT_CONFIG["settings"])
                return
            except (json.JSONDecodeError, OSError):
                pass  # Fall through to default

        # Create default config
        self._data = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
        self.save()

    def save(self) -> None:
        """Write current config to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    # ------------------------------------------------------------------
    # Mappings CRUD
    # ------------------------------------------------------------------

    def get_mappings(self) -> Dict[str, Dict[str, int]]:
        """Return all key→{x, y} mappings."""
        return dict(self._data.get("mappings", {}))

    def set_mapping(self, key: str, x: int, y: int) -> None:
        """Add or update a mapping and persist."""
        self._data["mappings"][key] = {"x": x, "y": y}
        self.save()

    def remove_mapping(self, key: str) -> bool:
        """Remove a mapping by key name. Returns True if it existed."""
        if key in self._data["mappings"]:
            del self._data["mappings"][key]
            self.save()
            return True
        return False

    def get_mapping(self, key: str) -> Optional[Tuple[int, int]]:
        """Return (x, y) for a key, or None."""
        m = self._data["mappings"].get(key)
        if m:
            return (m["x"], m["y"])
        return None

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def get_settings(self) -> Dict[str, Any]:
        """Return a copy of the settings dict."""
        return dict(self._data.get("settings", {}))

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Return a single setting value."""
        return self._data.get("settings", {}).get(key, default)

    def update_setting(self, key: str, value: Any) -> None:
        """Update a single setting and persist."""
        self._data.setdefault("settings", {})[key] = value
        self.save()
