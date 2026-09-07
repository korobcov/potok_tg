import logging
from pathlib import Path

from app.runtime_paths import APP_DIR

logger = logging.getLogger(__name__)

# Lives next to .env (see runtime_paths.APP_DIR) so it's editable without
# touching code or rebuilding the Windows .exe. See post_footer.example.txt
# for the format - it's appended to every post as-is (Telegram HTML), not
# escaped, so it may use Telegram's formatting tags (bold, italic, spoiler,
# blockquote, links, ...).
POST_FOOTER_FILE: Path = APP_DIR / "post_footer.txt"


def get_post_footer() -> str:
    """Reads the optional post-footer file, or "" if it doesn't exist."""
    try:
        return POST_FOOTER_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""
    except OSError as e:
        logger.warning(f"Failed to read {POST_FOOTER_FILE}: {e}")
        return ""
