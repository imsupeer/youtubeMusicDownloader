import pytest
from pydantic import ValidationError

from core.models import DownloadRequest, DownloadTask, ProbeRequest, TrackEntry


def test_download_task_accepts_allowed_bitrates():
    for kbps in (128, 192, 256, 320):
        task = DownloadTask(url="https://example.com", outdir="/tmp", bitrate_kbps=kbps)
        assert task.bitrate_kbps == kbps


def test_download_task_rejects_invalid_bitrate():
    with pytest.raises(ValidationError):
        DownloadTask(url="https://example.com", outdir="/tmp", bitrate_kbps=999)


def test_probe_request_requires_non_empty_url():
    with pytest.raises(ValidationError):
        ProbeRequest(url="")


def test_download_request_requires_at_least_one_track():
    with pytest.raises(ValidationError):
        DownloadRequest(outdir="/tmp/music", tracks=[])


def test_download_request_accepts_valid_payload():
    body = DownloadRequest(
        outdir="/tmp/music",
        bitrate_kbps=192,
        tracks=[TrackEntry(url="https://youtube.com/watch?v=abc", title="Song")],
    )
    assert body.bitrate_kbps == 192
    assert len(body.tracks) == 1
