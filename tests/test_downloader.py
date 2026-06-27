from unittest.mock import MagicMock, patch

from core.downloader import build_ydl_opts, download
from core.models import DownloadTask


def test_build_ydl_opts_includes_mp3_postprocessor():
    task = DownloadTask(
        url="https://youtube.com/watch?v=abc",
        outdir="/music",
        bitrate_kbps=256,
    )

    opts = build_ydl_opts(task)

    assert opts["format"] == "bestaudio/best"
    assert opts["quiet"] is True
    assert "music" in opts["outtmpl"]
    assert opts["postprocessors"][0]["preferredcodec"] == "mp3"
    assert opts["postprocessors"][0]["preferredquality"] == "256"
    assert opts["extractor_args"]["youtube"]["player_client"] == [
        "android",
        "web",
        "ios",
    ]
    assert "progress_hooks" not in opts


def test_build_ydl_opts_adds_progress_hook_when_provided():
    task = DownloadTask(url="https://example.com", outdir="/music")
    hook = lambda d: None

    opts = build_ydl_opts(task, hook)

    assert opts["progress_hooks"] == [hook]


@patch("core.downloader.YoutubeDL")
@patch("core.downloader.os.makedirs")
def test_download_creates_outdir_and_invokes_ytdlp(mock_makedirs, mock_ydl_cls):
    mock_ydl = MagicMock()
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.download.return_value = 0
    mock_ydl_cls.return_value = mock_ydl

    task = DownloadTask(url="https://youtube.com/watch?v=abc", outdir="/music/out")
    result = download(task)

    mock_makedirs.assert_called_once_with("/music/out", exist_ok=True)
    mock_ydl.download.assert_called_once_with(["https://youtube.com/watch?v=abc"])
    assert result == 0
