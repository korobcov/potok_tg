"""Path resolution that works both from source and as a frozen PyInstaller exe.

When PyInstaller builds a onefile executable, the app runs from a temporary
extraction directory (``sys._MEIPASS``) that changes on every launch, while
``sys.executable`` stays pointed at the actual, stable ``.exe`` location.
User-editable files (``.env``) must live next to the stable exe path;
read-only bundled resources (``ffmpeg.exe``) are shipped inside the temp
bundle.
"""
import sys
from pathlib import Path

IS_FROZEN = bool(getattr(sys, "frozen", False))

if IS_FROZEN:
    # Directory containing the actual .exe - stable across runs, where the
    # user keeps their .env file.
    APP_DIR = Path(sys.executable).resolve().parent
    # Directory PyInstaller extracted bundled data files into for this run.
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    # app/runtime_paths.py -> project root
    APP_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = APP_DIR

ENV_FILE = APP_DIR / ".env"


def find_ffmpeg() -> str | None:
    """Return a path to a bundled ffmpeg.exe, if one was packaged in."""
    for candidate in (BUNDLE_DIR / "ffmpeg.exe", APP_DIR / "ffmpeg.exe"):
        if candidate.is_file():
            return str(candidate)
    return None
