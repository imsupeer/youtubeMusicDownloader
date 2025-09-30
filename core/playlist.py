from yt_dlp import YoutubeDL


def probe(url: str):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": "discard_in_playlist",
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info is None:
        return {"type": "unknown", "entries": []}
    if "entries" in info:
        entries = []
        for e in info.get("entries") or []:
            if e is None:
                continue
            entries.append(
                {
                    "id": e.get("id"),
                    "title": e.get("title"),
                    "url": e.get("url") or e.get("webpage_url") or "",
                }
            )
        return {
            "type": "playlist",
            "title": info.get("title") or "",
            "entries": entries,
        }
    return {
        "type": "single",
        "title": info.get("title") or "",
        "entries": [{"id": info.get("id"), "title": info.get("title"), "url": url}],
    }
