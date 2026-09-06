import pytest
from unittest.mock import patch
from app.services.parser import parse_video_url


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
    # Real test against a public YouTube video URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = await parse_video_url(test_url)

    if result is not None:
        assert isinstance(result["title"], str)
        assert result["thumbnail_url"].startswith("http")
        assert "youtube" in result["url"]
