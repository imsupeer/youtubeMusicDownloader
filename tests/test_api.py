from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture(autouse=True)
def mock_background_download():
    with patch("core.queue.download", return_value=0):
        yield


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_get_config(client):
    response = client.get("/api/config")

    assert response.status_code == 200
    body = response.json()
    assert "default_outdir" in body
    assert body["default_bitrate"] == 192
    assert body["bitrates"] == [128, 192, 256, 320]


@patch("api.main.probe")
def test_probe_single_video(mock_probe, client, single_probe_result):
    mock_probe.return_value = single_probe_result

    response = client.post("/api/probe", json={"url": "https://youtube.com/watch?v=abc"})

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "single"
    assert body["title"] == "Test Song"
    assert len(body["entries"]) == 1


@patch("api.main.probe", side_effect=RuntimeError("blocked"))
def test_probe_returns_502_on_failure(mock_probe, client):
    response = client.post("/api/probe", json={"url": "https://youtube.com/watch?v=abc"})

    assert response.status_code == 502
    assert response.json()["detail"] == "blocked"


def test_probe_rejects_empty_url(client):
    response = client.post("/api/probe", json={"url": ""})

    assert response.status_code == 422


@patch("api.main.pick_folder", return_value="/chosen/folder")
def test_pick_folder_returns_path(mock_pick, client):
    response = client.post("/api/pick-folder", json={"initial_dir": "/start"})

    assert response.status_code == 200
    assert response.json() == {"path": "/chosen/folder"}
    mock_pick.assert_called_once()


@patch("api.main.pick_folder", return_value=None)
def test_pick_folder_returns_cancelled(mock_pick, client):
    response = client.post("/api/pick-folder", json={})

    assert response.status_code == 200
    assert response.json() == {"cancelled": True}


def test_download_queues_tracks(client):
    payload = {
        "outdir": "/tmp/music",
        "bitrate_kbps": 192,
        "tracks": [
            {"url": "https://youtube.com/watch?v=1", "title": "One"},
            {"url": "https://youtube.com/watch?v=2", "title": "Two"},
        ],
    }

    response = client.post("/api/download", json=payload)

    assert response.status_code == 200
    assert response.json()["queued"] == 2


def test_download_rejects_tracks_without_urls(client):
    payload = {
        "outdir": "/tmp/music",
        "bitrate_kbps": 192,
        "tracks": [{"url": "", "title": "Missing URL"}],
    }

    response = client.post("/api/download", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "No valid tracks to download"


def test_index_returns_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "YouTube MP3 Downloader" in response.text
