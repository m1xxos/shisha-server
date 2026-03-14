"""Unit tests for the downloader module."""
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import downloader as dl


# ── _safe_filename ────────────────────────────────────────────────────────────

class TestSafeFilename:
    def test_basic(self):
        assert dl._safe_filename("My DJ Set") == "My DJ Set"

    def test_strips_special_chars(self):
        result = dl._safe_filename("Hello/World:Test?")
        assert "/" not in result
        assert ":" not in result
        assert "?" not in result

    def test_empty_fallback(self):
        assert dl._safe_filename("!!!") == "audio"

    def test_keeps_allowed_chars(self):
        name = "Artist - Title (2024).mp3"
        result = dl._safe_filename(name)
        assert "-" in result
        assert "(" in result
        assert ")" in result
        assert "." in result

    def test_collapses_whitespace(self):
        result = dl._safe_filename("  too   many  spaces  ")
        assert "  " not in result
        assert result.startswith("too")


# ── _parse_time ───────────────────────────────────────────────────────────────

class TestParseTime:
    def test_none_passthrough(self):
        assert dl._parse_time(None) is None

    def test_mm_ss(self):
        assert dl._parse_time("1:30") == "1:30"

    def test_hh_mm_ss(self):
        assert dl._parse_time("01:30:00") == "01:30:00"

    def test_seconds_integer(self):
        assert dl._parse_time("90") == "90"

    def test_seconds_float(self):
        assert dl._parse_time("90.5") == "90.5"

    def test_strips_whitespace(self):
        assert dl._parse_time("  2:00  ") == "2:00"

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            dl._parse_time("not-a-time")

    def test_invalid_letters_raises(self):
        with pytest.raises(ValueError):
            dl._parse_time("1h30m")


# ── DownloadRequest ───────────────────────────────────────────────────────────

class TestDownloadRequest:
    def test_stores_fields(self):
        req = dl.DownloadRequest(
            url="https://example.com/video",
            start_time="1:00",
            end_time="2:00",
            title="My Set",
            artist="DJ X",
            album="Events",
        )
        assert req.url == "https://example.com/video"
        assert req.start_time == "1:00"
        assert req.end_time == "2:00"
        assert req.title == "My Set"
        assert req.artist == "DJ X"
        assert req.album == "Events"

    def test_optional_none_defaults(self):
        req = dl.DownloadRequest(url="https://example.com")
        assert req.start_time is None
        assert req.end_time is None
        assert req.title is None

    def test_invalid_time_propagates(self):
        with pytest.raises(ValueError):
            dl.DownloadRequest(url="https://example.com", start_time="bad")


# ── _find_cover ───────────────────────────────────────────────────────────────

class TestFindCover:
    def test_finds_jpg_in_tmpdir(self, tmp_path):
        jpg = tmp_path / "thumb.jpg"
        jpg.write_bytes(b"FAKEJPEG")
        result = dl._find_cover(tmp_path, None)
        assert result is not None
        mime, data = result
        assert mime == "image/jpeg"
        assert data == b"FAKEJPEG"

    def test_finds_png_in_tmpdir(self, tmp_path):
        png = tmp_path / "cover.png"
        png.write_bytes(b"FAKEPNG")
        result = dl._find_cover(tmp_path, None)
        assert result is not None
        mime, data = result
        assert mime == "image/png"
        assert data == b"FAKEPNG"

    def test_no_local_file_fetches_url(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.content = b"REMOTEJPEG"

        with patch("downloader.requests.get", return_value=mock_resp) as mock_get:
            result = dl._find_cover(tmp_path, "https://example.com/thumb.jpg")
            mock_get.assert_called_once()

        assert result is not None
        assert result[1] == b"REMOTEJPEG"

    def test_no_local_no_url_returns_none(self, tmp_path):
        assert dl._find_cover(tmp_path, None) is None

    def test_failed_url_returns_none(self, tmp_path):
        with patch("downloader.requests.get", side_effect=Exception("network error")):
            assert dl._find_cover(tmp_path, "https://example.com/img.jpg") is None


# ── download_and_process (integration-style with mocks) ──────────────────────

class TestDownloadAndProcess:
    """Test the main download_and_process flow with all external calls mocked."""

    def _make_fake_ydl(self, tmpdir: str, title="Test Track", uploader="Test Artist"):
        """Return a fake YoutubeDL context manager that creates a dummy mp3."""

        class FakeYDL:
            def __init__(self, opts):
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def extract_info(self, url, download=True):
                # Write a minimal valid MP3 (44 bytes header) into tmpdir
                mp3_path = Path(tmpdir) / "fakevideo.mp3"
                mp3_path.write_bytes(_minimal_mp3())
                return {
                    "title": title,
                    "uploader": uploader,
                    "thumbnail": None,
                    "id": "fakevideo",
                }

        return FakeYDL

    def test_successful_download_no_trim(self, tmp_path):
        music_dir = tmp_path / "music"
        music_dir.mkdir()

        with patch.dict(os.environ, {"OUTPUT_DIR": str(music_dir)}):
            with patch("downloader.OUTPUT_DIR", str(music_dir)):
                with tempfile.TemporaryDirectory() as real_tmp:
                    fake_ydl_class = self._make_fake_ydl(real_tmp)
                    with patch("downloader.yt_dlp.YoutubeDL", fake_ydl_class):
                        with patch("downloader._tag_mp3"):
                            req = dl.DownloadRequest(
                                url="https://youtube.com/watch?v=test",
                                title="Test Track",
                                artist="Test Artist",
                            )
                            # Patch tempfile so we control the tmp path
                            with patch("downloader.tempfile.TemporaryDirectory") as mock_td:
                                mock_td.return_value.__enter__ = lambda s: real_tmp
                                mock_td.return_value.__exit__ = MagicMock(return_value=False)
                                result = dl.download_and_process(req)

        assert result == "Test Track.mp3"
        assert (music_dir / "Test Track.mp3").exists()

    def test_no_mp3_raises(self, tmp_path):
        music_dir = tmp_path / "music"
        music_dir.mkdir()

        class FakeYDLEmpty:
            def __init__(self, opts):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
            def extract_info(self, url, download=True):
                return {"title": "X", "uploader": "Y", "thumbnail": None, "id": "x"}

        with patch("downloader.OUTPUT_DIR", str(music_dir)):
            with patch("downloader.yt_dlp.YoutubeDL", FakeYDLEmpty):
                req = dl.DownloadRequest(url="https://youtube.com/watch?v=test")
                with pytest.raises(RuntimeError, match="No MP3"):
                    dl.download_and_process(req)

    def test_trim_called_when_times_given(self, tmp_path):
        music_dir = tmp_path / "music"
        music_dir.mkdir()

        with tempfile.TemporaryDirectory() as real_tmp:
            fake_ydl_class = self._make_fake_ydl(real_tmp)
            with patch("downloader.OUTPUT_DIR", str(music_dir)):
                with patch("downloader.yt_dlp.YoutubeDL", fake_ydl_class):
                    with patch("downloader._tag_mp3"):
                        with patch("downloader.subprocess.run") as mock_run:
                            mock_run.return_value = MagicMock(returncode=0)
                            # Create fake trimmed.mp3 output when subprocess is called
                            def fake_run(cmd, **kwargs):
                                trimmed = Path(real_tmp) / "trimmed.mp3"
                                trimmed.write_bytes(_minimal_mp3())
                                return MagicMock(returncode=0)
                            mock_run.side_effect = fake_run

                            req = dl.DownloadRequest(
                                url="https://youtube.com/watch?v=test",
                                start_time="1:00",
                                end_time="2:00",
                            )
                            with patch("downloader.tempfile.TemporaryDirectory") as mock_td:
                                mock_td.return_value.__enter__ = lambda s: real_tmp
                                mock_td.return_value.__exit__ = MagicMock(return_value=False)
                                dl.download_and_process(req)

                            cmd_used = mock_run.call_args[0][0]
                            assert "-ss" in cmd_used
                            assert "1:00" in cmd_used
                            assert "-to" in cmd_used
                            assert "2:00" in cmd_used

    def test_trim_ffmpeg_failure_raises(self, tmp_path):
        music_dir = tmp_path / "music"
        music_dir.mkdir()

        with tempfile.TemporaryDirectory() as real_tmp:
            fake_ydl_class = self._make_fake_ydl(real_tmp)
            with patch("downloader.OUTPUT_DIR", str(music_dir)):
                with patch("downloader.yt_dlp.YoutubeDL", fake_ydl_class):
                    with patch("downloader.subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(returncode=1, stderr="ffmpeg error")
                        req = dl.DownloadRequest(
                            url="https://youtube.com/watch?v=test",
                            start_time="1:00",
                        )
                        with patch("downloader.tempfile.TemporaryDirectory") as mock_td:
                            mock_td.return_value.__enter__ = lambda s: real_tmp
                            mock_td.return_value.__exit__ = MagicMock(return_value=False)
                            with pytest.raises(RuntimeError, match="ffmpeg trim failed"):
                                dl.download_and_process(req)

    def test_duplicate_filename_gets_counter(self, tmp_path):
        music_dir = tmp_path / "music"
        music_dir.mkdir()
        # Pre-create the expected output file
        (music_dir / "Test Track.mp3").write_bytes(b"existing")

        with tempfile.TemporaryDirectory() as real_tmp:
            fake_ydl_class = self._make_fake_ydl(real_tmp, title="Test Track")
            with patch("downloader.OUTPUT_DIR", str(music_dir)):
                with patch("downloader.yt_dlp.YoutubeDL", fake_ydl_class):
                    with patch("downloader._tag_mp3"):
                        req = dl.DownloadRequest(
                            url="https://youtube.com/watch?v=test",
                            title="Test Track",
                        )
                        with patch("downloader.tempfile.TemporaryDirectory") as mock_td:
                            mock_td.return_value.__enter__ = lambda s: real_tmp
                            mock_td.return_value.__exit__ = MagicMock(return_value=False)
                            result = dl.download_and_process(req)

        assert result == "Test Track (1).mp3"


# ── helpers ───────────────────────────────────────────────────────────────────

def _minimal_mp3() -> bytes:
    """Return a minimal (but parseable by most code) MP3 frame header."""
    # ID3v2.3 tag + one silent MPEG frame – enough to be a valid file
    # ID3 header: "ID3" + version 2.3 + flags 0 + size 0
    id3_header = b"ID3\x03\x00\x00\x00\x00\x00\x00"
    # Minimal silent MP3 frame (MPEG1 Layer3 128kbps 44100Hz stereo)
    mp3_frame = b"\xff\xfb\x90\x00" + b"\x00" * 413
    return id3_header + mp3_frame
