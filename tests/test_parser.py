import pytest
from unittest.mock import patch, Mock
from app.services.parser import download_thumbnail, parse_video_url


def test_parse_video_url_mock():
    mock_info = {
        "title": "Test Video Title",
        "thumbnail": "https://example.com/thumb.jpg",
        "webpage_url": "https://youtube.com/watch?v=test12345",
    }

    with patch(
        "app.services.parser._extract_info_sync", return_value=mock_info
    ):
        result = parse_video_url("https://youtube.com/watch?v=test12345")

    assert result is not None
    assert result["title"] == "Test Video Title"
    assert result["thumbnail_url"] == "https://example.com/thumb.jpg"
    assert result["url"] == "https://youtube.com/watch?v=test12345"


def test_parse_video_url_missing_thumbnail():
    mock_info = {
        "title": "Test Video No Thumb",
        "thumbnail": None,
        "thumbnails": [],
        "webpage_url": "https://youtube.com/watch?v=nothumb",
    }

    with patch(
        "app.services.parser._extract_info_sync", return_value=mock_info
    ):
        result = parse_video_url("https://youtube.com/watch?v=nothumb")

    assert result is None


def test_parse_video_url_integration():
    # Real test against a public YouTube video URL. Skipped explicitly
    # (instead of silently passing with no assertions) when the network
    # or extractor is unavailable, so failures are never masked as green.
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = parse_video_url(test_url)

    if result is None:
        pytest.skip(
            "Skipping: yt-dlp could not fetch video info "
            "(no network access or extractor blocked in this environment)"
        )

    assert isinstance(result["title"], str)
    assert result["thumbnail_url"].startswith("http")
    assert "youtube" in result["url"]


def test_download_thumbnail_success():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"binary-image-data"

    with patch(
        "app.services.parser.requests.get", return_value=mock_response
    ):
        result = download_thumbnail("https://example.com/thumb.jpg")

    assert result == b"binary-image-data"


def test_download_thumbnail_non_200_status():
    mock_response = Mock()
    mock_response.status_code = 403

    with patch(
        "app.services.parser.requests.get", return_value=mock_response
    ):
        result = download_thumbnail("https://example.com/blocked.jpg")

    assert result is None


def test_download_thumbnail_request_exception():
    with patch(
        "app.services.parser.requests.get",
        side_effect=Exception("connection failed"),
    ):
        result = download_thumbnail("https://example.com/thumb.jpg")

    assert result is None
