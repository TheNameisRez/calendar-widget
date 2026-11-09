"""Central settings and file paths."""

import os
from pathlib import Path

APP_NAME = "calendar-widget"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Google permission: read the calendar AND create events.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Appearance
DAYS = 5                 # number of days shown
REFRESH_MINUTES = 5      # automatic refresh interval
WIDTH_FRACTION = 0.2     # widget width relative to the screen width


def data_dir() -> Path:
    """Folder that holds credentials.json and token.json.

    Lookup order:
      1. Environment variable CALENDAR_WIDGET_DIR
      2. ~/.config/calendar-widget  (or $XDG_CONFIG_HOME)
      3. The project folder, if a credentials.json already lies there
         (compatibility with the first version)
    """
    env = os.environ.get("CALENDAR_WIDGET_DIR")
    if env:
        return Path(env).expanduser()

    xdg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    default = xdg / APP_NAME
    if (not (default / "credentials.json").exists()
            and (PROJECT_ROOT / "credentials.json").exists()):
        return PROJECT_ROOT
    return default


def credentials_path() -> Path:
    return data_dir() / "credentials.json"


def token_path() -> Path:
    return data_dir() / "token.json"
