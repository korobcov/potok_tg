import logging
from typing import Any, Dict, Optional
import requests
import yt_dlp

from app.runtime_paths import find_ffmpeg

logger = logging.getLogger(__name__)

THUMBNAIL_DOWNLOAD_TIMEOUT = 15
THUMBNAIL_DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# On the Windows native build, ffmpeg.exe ships bundled next to the app
# instead of being installed system-wide (unlike Docker/Linux, where it's
# expected on PATH already).
_BUNDLED_FFMPEG = find_ffmpeg()


def _extract_info_sync(url: str) -> Dict[str, Any]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }
    if _BUNDLED_FFMPEG:
        ydl_opts["ffmpeg_location"] = _BUNDLED_FFMPEG
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def parse_video_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parses a video URL using yt-dlp and extracts title, thumbnail_url,
    and web_url.
    Returns a dict with {'title': ..., 'thumbnail_url': ..., 'url': ...}
    or None if parsing fails/thumbnail missing.
    """
    try:
        info = _extract_info_sync(url)
        if not info:
            logger.error(f"Failed to retrieve info for URL: {url}")
            return None

        title = info.get("title") or "Без названия"
        thumbnail_url = info.get("thumbnail")

        # If thumbnail is missing in 'thumbnail', try checking 'thumbnails'
        if not thumbnail_url and info.get("thumbnails"):
            thumbnails = info.get("thumbnails")
            if isinstance(thumbnails, list) and len(thumbnails) > 0:
                thumbnail_url = thumbnails[-1].get("url")

        if not thumbnail_url:
            logger.warning(f"No thumbnail found for URL: {url}")
            return None

        web_url = info.get("webpage_url") or url

        return {
            "title": title,
            "thumbnail_url": thumbnail_url,
            "url": web_url,
        }
    except Exception as e:
        logger.error(f"Error parsing URL {url}: {e}")
        return None


def download_thumbnail(url: str) -> Optional[bytes]:
    """
    Downloads thumbnail bytes ourselves instead of letting Telegram fetch
    the URL directly, since some sources (VK, Instagram) block hotlinking
    without a browser-like User-Agent.
    Returns the raw bytes, or None if the download fails.
    """
    try:
        response = requests.get(
            url,
            headers=THUMBNAIL_DOWNLOAD_HEADERS,
            timeout=THUMBNAIL_DOWNLOAD_TIMEOUT,
        )
        if response.status_code != 200:
            logger.warning(
                f"Thumbnail download for {url} returned "
                f"status {response.status_code}"
            )
            return None
        return response.content
    except Exception as e:
        logger.error(f"Error downloading thumbnail {url}: {e}")
        return None
