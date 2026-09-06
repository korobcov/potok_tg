import asyncio
import logging
from typing import Dict, Any, Optional
import yt_dlp

logger = logging.getLogger(__name__)


def _extract_info_sync(url: str) -> Dict[str, Any]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


async def parse_video_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parses a video URL using yt-dlp and extracts title, thumbnail_url,
    and web_url.
    Returns a dict with {'title': ..., 'thumbnail_url': ..., 'url': ...}
    or None if parsing fails/thumbnail missing.
    """
    try:
        info = await asyncio.to_thread(_extract_info_sync, url)
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
