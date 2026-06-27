from yt_dlp import YoutubeDL

from core.models import ProbeResult, TrackEntry
from core.ytdlp_opts import build_base_ytdl_opts


def probe(url: str) -> ProbeResult:
    ydl_opts = {
        **build_base_ytdl_opts(),
        "skip_download": True,
        "extract_flat": "discard_in_playlist",
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        return ProbeResult(type="unknown")

    if "entries" in info:
        entries: list[TrackEntry] = []
        for entry in info.get("entries") or []:
            if entry is None:
                continue
            entries.append(
                TrackEntry(
                    id=entry.get("id"),
                    title=entry.get("title"),
                    url=entry.get("url") or entry.get("webpage_url") or "",
                )
            )
        return ProbeResult(
            type="playlist",
            title=info.get("title") or "",
            entries=entries,
        )

    return ProbeResult(
        type="single",
        title=info.get("title") or "",
        entries=[
            TrackEntry(
                id=info.get("id"),
                title=info.get("title"),
                url=url,
            )
        ],
    )
