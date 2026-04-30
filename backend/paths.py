import os
import sys
import json
from pathlib import Path

def get_app_data_dir() -> Path:
    if sys.platform == "win32":
        base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base_dir = os.path.expanduser("~")
    app_dir = Path(base_dir) / "Edu MeetLog"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

APP_DATA_DIR = get_app_data_dir()
RECORDINGS_DIR = APP_DATA_DIR / "recordings"
QUEUE_DIR = APP_DATA_DIR / "queue"
CONFIG_DIR = APP_DATA_DIR / "config"
LABELS_FILE = CONFIG_DIR / "labels.json"
CLIENTS_FILE = CONFIG_DIR / "clients.json"
PEOPLE_FILE = CONFIG_DIR / "people.json"
STAKEHOLDERS_FILE = CONFIG_DIR / "stakeholders.json"
ACTION_ITEMS_FILE = CONFIG_DIR / "action_items.json"

def get_transcripts_dir() -> Path:
    """Returns custom output dir from settings or default."""
    settings_file = CONFIG_DIR / "settings.json"
    if settings_file.exists():
        try:
            s = json.loads(settings_file.read_text(encoding="utf-8"))
            custom = s.get("output_folder", "")
            if custom:
                p = Path(custom)
                p.mkdir(parents=True, exist_ok=True)
                return p
        except Exception:
            pass
    default = APP_DATA_DIR / "transcripts"
    default.mkdir(parents=True, exist_ok=True)
    return default

TRANSCRIPTS_DIR = get_transcripts_dir()

RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
