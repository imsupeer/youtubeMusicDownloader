import os
from typing import Callable, Optional

from yt_dlp import YoutubeDL

from core.models import DownloadTask
from core.ytdlp_opts import build_base_ytdl_opts


def build_ydl_opts(
    task: DownloadTask, progress: Optional[Callable[[dict], None]] = None
) -> dict:
    opts = {
        **build_base_ytdl_opts(),
        "format": "bestaudio/best",
        "outtmpl": os.path.join(task.outdir, task.filename_template),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": str(task.bitrate_kbps),
            },
            {"key": "FFmpegMetadata"},
        ],
    }
    if progress:
        opts["progress_hooks"] = [progress]
    return opts


def download(
    task: DownloadTask, progress_cb: Optional[Callable[[dict], None]] = None
) -> int:
    os.makedirs(task.outdir, exist_ok=True)
    with YoutubeDL(build_ydl_opts(task, progress_cb)) as ydl:
        return ydl.download([task.url])
