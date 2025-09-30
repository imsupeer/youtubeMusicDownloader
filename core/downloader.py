import os
from typing import Callable, Optional, Dict
from yt_dlp import YoutubeDL


class DownloadTask:
    def __init__(
        self,
        url: str,
        bitrate_kbps: int,
        outdir: str,
        filename_template: Optional[str] = None,
    ):
        self.url = url
        self.bitrate_kbps = bitrate_kbps
        self.outdir = outdir
        self.filename_template = filename_template or "%(title)s-%(id)s.%(ext)s"


def build_ydl_opts(
    task: DownloadTask, progress: Optional[Callable[[Dict], None]] = None
):
    ppq = str(task.bitrate_kbps)
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(task.outdir, task.filename_template),
        "quiet": True,
        "noprogress": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": ppq,
            },
            {"key": "FFmpegMetadata"},
        ],
    }
    if progress:
        opts["progress_hooks"] = [progress]
    return opts


def download(task: DownloadTask, progress_cb: Optional[Callable[[Dict], None]] = None):
    os.makedirs(task.outdir, exist_ok=True)
    with YoutubeDL(build_ydl_opts(task, progress_cb)) as ydl:
        return ydl.download([task.url])
