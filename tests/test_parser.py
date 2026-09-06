import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.parser import download_thumbnail, parse_video_url


def _make_mock_session(mock_response):
    mock_get_cm = MagicMock()
    mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_get_cm)

    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_session_cm


@pytest.mark.asyncio
async def test_parse_video_url_mock():
    mock_info = {
        "title": "Test Video Title",
        "thumbnail": "https://example.com/thumb.jpg",
        "webpage_url": "https://youtube.com/watch?v=test12345",
    }

    with patch(
        "app.services.parser._extract_info_sync", return_value=mock_info
    ):
        result = await parse_video_url(
            "https://youtube.com/watch?v=test12345"
        )

    assert result is not None
    assert result["title"] == "Test Video Title"
    assert result["thumbnail_url"] == "https://example.com/thumb.jpg"
    assert result["url"] == "https://youtube.com/watch?v=test12345"


@pytest.mark.asyncio
async def test_parse_video_url_missing_thumbnail():
    mock_info = {
        "title": "Test Video No Thumb",
        "thumbnail": None,
        "thumbnails": [],
        "webpage_url": "https://youtube.com/watch?v=nothumb",
    }

    with patch(
        "app.services.parser._extract_info_sync", return_value=mock_info
    ):
        result = await parse_video_url(
            "https://youtube.com/watch?v=nothumb"
        )

    assert result is None


@pytest.mark.asyncio
async def test_parse_video_url_integration():
    # Real test against a public YouTube video URL. Skipped explicitly
    # (instead of silently passing with no assertions) when the network
    # or extractor is unavailable, so failures are never masked as green.
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = await parse_video_url(test_url)

    if result is None:
        pytest.skip(
            "Skipping: yt-dlp could not fetch video info "
            "(no network access or extractor blocked in this environment)"
        )

    assert isinstance(result["title"], str)
    assert result["thumbnail_url"].startswith("http")
    assert "youtube" in result["url"]


@pytest.mark.asyncio
async def test_download_thumbnail_success():
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"binary-image-data")

    mock_session_cm = _make_mock_session(mock_response)

    with patch(
        "app.services.parser.aiohttp.ClientSession",
        return_value=mock_session_cm,
    ):
        result = await download_thumbnail("https://example.com/thumb.jpg")

    assert result == b"binary-image-data"


@pytest.mark.asyncio
async def test_download_thumbnail_non_200_status():
    mock_response = MagicMock()
    mock_response.status = 403

    mock_session_cm = _make_mock_session(mock_response)

    with patch(
        "app.services.parser.aiohttp.ClientSession",
        return_value=mock_session_cm,
    ):
        result = await download_thumbnail("https://example.com/blocked.jpg")

    assert result is None


@pytest.mark.asyncio
async def test_download_thumbnail_request_exception():
    with patch(
        "app.services.parser.aiohttp.ClientSession",
        side_effect=Exception("connection failed"),
    ):
        result = await download_thumbnail("https://example.com/thumb.jpg")

    assert result is None
