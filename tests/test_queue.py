import asyncio
from unittest.mock import patch

import pytest

from core.models import DownloadTask
from core.queue import DownloadManager


async def run_single_download(manager: DownloadManager, task: DownloadTask) -> list:
    events = []

    async def reader():
        async for event in manager.subscribe():
            events.append(event)
            if event.type in ("idle", "error"):
                break

    await manager.start()
    reader_task = asyncio.create_task(reader())
    await asyncio.sleep(0)
    await manager.enqueue([task])
    await asyncio.wait_for(reader_task, timeout=2.0)
    await manager.stop()
    return events


@pytest.mark.asyncio
@patch("core.queue.download", return_value=0)
async def test_download_manager_emits_lifecycle_events(mock_download):
    task = DownloadTask(
        url="https://youtube.com/watch?v=abc",
        outdir="/tmp",
        title="My Song",
    )

    events = await run_single_download(DownloadManager(), task)
    types = [event.type for event in events]

    assert "started" in types
    assert "completed" in types
    assert types[-1] == "idle"
    mock_download.assert_called_once()


@pytest.mark.asyncio
@patch("core.queue.download", side_effect=RuntimeError("network down"))
async def test_download_manager_emits_error_event(mock_download):
    task = DownloadTask(url="https://youtube.com/watch?v=fail", outdir="/tmp")

    events = await run_single_download(DownloadManager(), task)
    error_events = [event for event in events if event.type == "error"]

    assert len(error_events) == 1
    assert "network down" in error_events[0].message
