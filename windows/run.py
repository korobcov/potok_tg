"""PyInstaller entry point.

Lives in windows/ (not project root) to keep build tooling out of the app
package, and inserts the project root onto sys.path so `app.*` imports
resolve the same way they do when PyInstaller's Analysis step discovers them
at build time.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import main  # noqa: E402

if __name__ == "__main__":
    main()
