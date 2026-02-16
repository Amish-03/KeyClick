# KeyClick

A Windows desktop utility that maps keyboard keys to mouse clicks at preconfigured screen coordinates. Designed for controlling the **Valeton GP100 editor** by switching patches via simulated mouse clicks.

## Features

- 🎹 **Global key listening** — map any key to a screen coordinate
- 🖱️ **Automated mouse clicks** — cursor moves, clicks, and returns to original position
- 🎨 **Dark-themed GUI** — built with PyQt6
- 💾 **Persistent config** — mappings saved to `config.json` automatically
- 🔒 **Foreground window check** — optionally only fire when the target app is focused
- 📌 **System tray** — minimize to tray, keep running in background
- ⏸️ **Enable / Disable** — pause the system without removing mappings

## Requirements

- Python 3.10+
- Windows 10/11

## Installation

```bash
git clone https://github.com/Amish-03/KeyClick.git
cd KeyClick
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

1. Click **"Add / Configure Key"**
2. Press the key you want to map (e.g. `F1`)
3. Click on the target screen position
4. Done — pressing that key will now click that spot

### Desktop Shortcut

To create a desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
```

## Configuration

Settings are stored in `config.json` (auto-created on first run):

```json
{
  "mappings": {
    "f1": { "x": 800, "y": 500 },
    "f2": { "x": 850, "y": 500 }
  },
  "settings": {
    "restore_mouse_position": true,
    "require_foreground_window": false,
    "target_window_title": "Valeton"
  }
}
```

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Entry point & application controller |
| `ui.py` | PyQt6 GUI with dark theme & system tray |
| `state_machine.py` | App state management (NORMAL / CONFIG / DISABLED) |
| `input_listener.py` | Global keyboard & mouse capture via pynput |
| `action_executor.py` | Mouse move, click, and restore |
| `mapping_manager.py` | CRUD for key→coordinate mappings |
| `config_manager.py` | JSON config persistence |

## License

MIT
