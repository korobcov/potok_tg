import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp
import yt_dlp

logger = logging.getLogger(__name__)

THUMBNAIL_DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=15)
THUMBNAIL_DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


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


async def download_thumbnail(url: str) -> Optional[bytes]:
    """
    Downloads thumbnail bytes ourselves instead of letting Telegram fetch
    the URL directly, since some sources (VK, Instagram) block hotlinking
    without a browser-like User-Agent.
    Returns the raw bytes, or None if the download fails.
    """
    try:
        async with aiohttp.ClientSession(
            timeout=THUMBNAIL_DOWNLOAD_TIMEOUT
        ) as session:
            async with session.get(
                url, headers=THUMBNAIL_DOWNLOAD_HEADERS
            ) as response:
                if response.status != 200:
                    logger.warning(
                        f"Thumbnail download for {url} returned "
                        f"status {response.status}"
                    )
                    return None
                return await response.read()
    except Exception as e:
        logger.error(f"Error downloading thumbnail {url}: {e}")
        return None
