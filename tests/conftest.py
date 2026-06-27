import pytest

from core.models import ProbeResult, TrackEntry


@pytest.fixture
def track_entry():
    return TrackEntry(id="abc123", title="Test Song", url="https://youtube.com/watch?v=abc123")


@pytest.fixture
def single_probe_result(track_entry):
    return ProbeResult(type="single", title="Test Song", entries=[track_entry])


@pytest.fixture
def playlist_probe_result():
    return ProbeResult(
        type="playlist",
        title="My Playlist",
        entries=[
            TrackEntry(id="1", title="Track 1", url="https://youtube.com/watch?v=1"),
            TrackEntry(id="2", title="Track 2", url="https://youtube.com/watch?v=2"),
        ],
    )


@pytest.fixture
def sample_single_ytdlp_info():
    return {
        "id": "abc123",
        "title": "Test Song",
    }


@pytest.fixture
def sample_playlist_ytdlp_info():
    return {
        "title": "My Playlist",
        "entries": [
            {"id": "1", "title": "Track 1", "url": "https://youtube.com/watch?v=1"},
            {"id": "2", "title": "Track 2", "webpage_url": "https://youtube.com/watch?v=2"},
            None,
        ],
    }
