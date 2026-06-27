import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.folders import pick_folder
from core.models import DownloadRequest, DownloadTask, PickFolderRequest, ProbeRequest
from core.playlist import probe
from core.queue import DownloadManager

STATIC_DIR = Path(__file__).parent / "static"


def create_app(download_manager: DownloadManager | None = None) -> FastAPI:
    manager = download_manager or DownloadManager()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await manager.start()
        yield
        await manager.stop()

    app = FastAPI(
        title="YouTube MP3 Downloader",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/config")
    async def get_config():
        return {
            "default_outdir": str(settings.default_outdir),
            "default_bitrate": settings.default_bitrate,
            "bitrates": [128, 192, 256, 320],
        }

    @app.post("/api/probe")
    async def api_probe(body: ProbeRequest):
        url = body.url.strip()
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        try:
            result = await asyncio.to_thread(probe, url)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return result

    @app.post("/api/pick-folder")
    async def api_pick_folder(body: PickFolderRequest | None = None):
        initial = (body.initial_dir if body and body.initial_dir else None) or str(
            settings.default_outdir
        )
        path = await asyncio.to_thread(pick_folder, initial)
        if not path:
            return {"cancelled": True}
        return {"path": path}

    @app.post("/api/download")
    async def api_download(body: DownloadRequest):
        tasks = [
            DownloadTask(
                url=track.url,
                title=track.title,
                bitrate_kbps=body.bitrate_kbps,
                outdir=body.outdir,
            )
            for track in body.tracks
            if track.url
        ]
        if not tasks:
            raise HTTPException(status_code=400, detail="No valid tracks to download")
        count = await manager.enqueue(tasks)
        return {"queued": count}

    @app.get("/api/events")
    async def api_events():
        async def stream():
            async for event in manager.subscribe():
                payload = json.dumps(event.model_dump())
                yield f"data: {payload}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    return app


app = create_app()
