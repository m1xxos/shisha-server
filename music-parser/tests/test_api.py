"""Integration tests for the FastAPI endpoints."""
import sys
import os

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Insert app dir so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import main as app_module
from main import app, _jobs

client = TestClient(app, raise_server_exceptions=False)


# ── Helper ────────────────────────────────────────────────────────────────────

def _clear_jobs():
    _jobs.clear()


# ── POST /api/download ────────────────────────────────────────────────────────

class TestCreateDownload:
    def setup_method(self):
        _clear_jobs()

    def test_returns_job_id(self):
        with patch("main._run_download"):
            resp = client.post("/api/download", json={"url": "https://youtube.com/watch?v=test"})
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert len(data["job_id"]) == 36  # UUID4

    def test_empty_url_rejected(self):
        resp = client.post("/api/download", json={"url": "   "})
        assert resp.status_code == 422

    def test_missing_url_rejected(self):
        resp = client.post("/api/download", json={})
        assert resp.status_code == 422

    def test_optional_fields_accepted(self):
        with patch("main._run_download"):
            resp = client.post("/api/download", json={
                "url": "https://soundcloud.com/artist/track",
                "start_time": "1:00",
                "end_time": "2:30",
                "title": "My Set",
                "artist": "DJ Test",
                "album": "Events 2024",
            })
        assert resp.status_code == 202

    def test_job_created_as_pending(self):
        with patch("main._run_download"):
            resp = client.post("/api/download", json={"url": "https://youtube.com/watch?v=x"})
        job_id = resp.json()["job_id"]
        assert _jobs[job_id]["status"] == "pending"


# ── GET /api/jobs/{job_id} ────────────────────────────────────────────────────

class TestGetJob:
    def setup_method(self):
        _clear_jobs()

    def test_unknown_job_returns_404(self):
        resp = client.get("/api/jobs/nonexistent-id")
        assert resp.status_code == 404

    def test_pending_job_returned(self):
        _jobs["abc"] = {"status": "pending", "message": "Queued"}
        resp = client.get("/api/jobs/abc")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    def test_done_job_returned(self):
        _jobs["xyz"] = {"status": "done", "message": "Saved: track.mp3", "file": "track.mp3"}
        resp = client.get("/api/jobs/xyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["file"] == "track.mp3"

    def test_error_job_returned(self):
        _jobs["err"] = {"status": "error", "message": "Download failed"}
        resp = client.get("/api/jobs/err")
        assert resp.status_code == 200
        assert resp.json()["status"] == "error"


# ── _run_download (background task) ──────────────────────────────────────────

class TestRunDownload:
    def setup_method(self):
        _clear_jobs()

    @pytest.mark.anyio
    async def test_sets_done_on_success(self):
        from main import _run_download, _jobs, DownloadPayload

        payload = DownloadPayload(url="https://youtube.com/watch?v=test")
        _jobs["j1"] = {"status": "pending", "message": "Queued"}

        with patch("main.download_and_process", return_value="track.mp3") as mock_dp:
            await _run_download("j1", payload)

        assert _jobs["j1"]["status"] == "done"
        assert "track.mp3" in _jobs["j1"]["message"]

    @pytest.mark.anyio
    async def test_sets_error_on_exception(self):
        from main import _run_download, _jobs, DownloadPayload

        payload = DownloadPayload(url="https://youtube.com/watch?v=test")
        _jobs["j2"] = {"status": "pending", "message": "Queued"}

        with patch("main.download_and_process", side_effect=RuntimeError("oops")):
            await _run_download("j2", payload)

        assert _jobs["j2"]["status"] == "error"
        assert "oops" in _jobs["j2"]["message"]


# ── Static files ──────────────────────────────────────────────────────────────

class TestStaticFiles:
    def test_index_html_served(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Music Parser" in resp.text

    def test_app_js_served(self):
        resp = client.get("/app.js")
        assert resp.status_code == 200
        assert "startDownload" in resp.text
