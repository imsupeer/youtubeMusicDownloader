import asyncio
from asyncio import Queue
from typing import AsyncIterator

from core.downloader import download
from core.models import DownloadTask, ProgressEvent


class DownloadManager:
    def __init__(self) -> None:
        self._task_queue: Queue[DownloadTask | None] = Queue()
        self._subscribers: set[Queue[ProgressEvent]] = set()
        self._worker_task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def start(self) -> None:
        if self._worker_task is None:
            self._loop = asyncio.get_running_loop()
            self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._worker_task is not None:
            await self._task_queue.put(None)
            await self._worker_task
            self._worker_task = None

    async def enqueue(self, tasks: list[DownloadTask]) -> int:
        for task in tasks:
            await self._task_queue.put(task)
        return len(tasks)

    async def subscribe(self) -> AsyncIterator[ProgressEvent]:
        channel: Queue[ProgressEvent] = asyncio.Queue()
        self._subscribers.add(channel)
        try:
            while True:
                yield await channel.get()
        finally:
            self._subscribers.discard(channel)

    async def _emit(self, event: ProgressEvent) -> None:
        for channel in list(self._subscribers):
            await channel.put(event)

    async def _worker(self) -> None:
        assert self._loop is not None
        loop = self._loop

        while True:
            task = await self._task_queue.get()
            if task is None:
                break

            title = task.title or task.url

            await self._emit(
                ProgressEvent(
                    type="started",
                    title=title,
                    message=f"Starting {title}",
                    queue_remaining=self._task_queue.qsize(),
                )
            )

            def progress_hook(data: dict) -> None:
                if data.get("status") != "downloading":
                    return
                percent_str = data.get("_percent_str", "0").strip().replace("%", "")
                try:
                    percent = float(percent_str)
                except ValueError:
                    percent = 0.0
                event = ProgressEvent(
                    type="progress",
                    filename=data.get("filename") or "",
                    percent=percent,
                    title=title,
                    message=f"Downloading {title}",
                    queue_remaining=self._task_queue.qsize(),
                )
                asyncio.run_coroutine_threadsafe(self._emit(event), loop)

            try:
                await loop.run_in_executor(None, download, task, progress_hook)
                await self._emit(
                    ProgressEvent(
                        type="completed",
                        title=title,
                        percent=100.0,
                        message=f"Finished {title}",
                        queue_remaining=self._task_queue.qsize(),
                    )
                )
            except Exception as exc:
                await self._emit(
                    ProgressEvent(
                        type="error",
                        title=title,
                        message=str(exc),
                        queue_remaining=self._task_queue.qsize(),
                    )
                )
            finally:
                self._task_queue.task_done()
                if self._task_queue.empty():
                    await self._emit(
                        ProgressEvent(type="idle", message="All downloads complete")
                    )
