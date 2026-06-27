from unittest.mock import MagicMock, patch

from core.models import ProbeResult, TrackEntry
from core.playlist import probe


@patch("core.playlist.YoutubeDL")
def test_probe_returns_unknown_when_info_is_none(mock_ydl_cls):
    mock_ydl = MagicMock()
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = None
    mock_ydl_cls.return_value = mock_ydl

    result = probe("https://youtube.com/watch?v=missing")

    assert result == ProbeResult(type="unknown")


@patch("core.playlist.YoutubeDL")
def test_probe_single_video(mock_ydl_cls, sample_single_ytdlp_info):
    mock_ydl = MagicMock()
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = sample_single_ytdlp_info
    mock_ydl_cls.return_value = mock_ydl

    url = "https://youtube.com/watch?v=abc123"
    result = probe(url)

    assert result.type == "single"
    assert result.title == "Test Song"
    assert len(result.entries) == 1
    assert result.entries[0] == TrackEntry(
        id="abc123", title="Test Song", url=url
    )


@patch("core.playlist.YoutubeDL")
def test_probe_playlist_skips_null_entries(mock_ydl_cls, sample_playlist_ytdlp_info):
    mock_ydl = MagicMock()
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.return_value = sample_playlist_ytdlp_info
    mock_ydl_cls.return_value = mock_ydl

    result = probe("https://youtube.com/playlist?list=xyz")

    assert result.type == "playlist"
    assert result.title == "My Playlist"
    assert len(result.entries) == 2
    assert result.entries[0].title == "Track 1"
    assert result.entries[1].url == "https://youtube.com/watch?v=2"
