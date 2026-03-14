"""Audio downloader and processor using yt-dlp and ffmpeg."""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import requests
import yt_dlp
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
from mutagen.mp3 import MP3

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/music")


def _safe_filename(name: str) -> str:
    """Return a filesystem-safe version of *name*."""
    safe = re.sub(r'[^\w\s\-().]', '', name).strip()
    safe = re.sub(r'\s+', ' ', safe)
    return safe or "audio"


def _parse_time(value: Optional[str]) -> Optional[str]:
    """Validate and normalise a time string (HH:MM:SS or MM:SS or seconds)."""
    if value is None:
        return None
    value = value.strip()
    # Already in HH:MM:SS / MM:SS format
    if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', value):
        return value
    # Pure seconds
    if re.match(r'^\d+(\.\d+)?$', value):
        return value
    raise ValueError(
        f"Invalid time format '{value}'. Use HH:MM:SS, MM:SS, or seconds."
    )


class DownloadRequest:
    """Holds all parameters for a single download job."""

    def __init__(
        self,
        url: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
    ):
        self.url = url
        self.start_time = _parse_time(start_time)
        self.end_time = _parse_time(end_time)
        self.title = title
        self.artist = artist
        self.album = album


def download_and_process(req: DownloadRequest) -> str:
    """Download, trim, tag and save audio. Returns the saved filename."""
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # ── 1. Download ──────────────────────────────────────────────────────
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(tmp / "%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
            "writethumbnail": True,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)

        title = req.title or info.get("title") or "Unknown"
        artist = req.artist or info.get("uploader") or info.get("creator") or "Unknown"
        album = req.album or info.get("album") or title
        thumbnail_url: Optional[str] = info.get("thumbnail")

        # ── 2. Locate downloaded MP3 ─────────────────────────────────────────
        mp3_files = list(tmp.glob("*.mp3"))
        if not mp3_files:
            raise RuntimeError("No MP3 produced after download.")
        source_mp3 = mp3_files[0]

        # ── 3. Trim (optional) ───────────────────────────────────────────────
        if req.start_time or req.end_time:
            trimmed_mp3 = tmp / "trimmed.mp3"
            cmd = ["ffmpeg", "-y", "-i", str(source_mp3)]
            if req.start_time:
                cmd += ["-ss", req.start_time]
            if req.end_time:
                cmd += ["-to", req.end_time]
            cmd += ["-acodec", "libmp3lame", "-q:a", "2", str(trimmed_mp3)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg trim failed: {result.stderr}")
            source_mp3 = trimmed_mp3

        # ── 4. Copy to output dir ────────────────────────────────────────────
        safe_title = _safe_filename(title)
        dest = output_dir / f"{safe_title}.mp3"
        # Avoid overwriting – append a counter if needed
        counter = 1
        while dest.exists():
            dest = output_dir / f"{safe_title} ({counter}).mp3"
            counter += 1
        shutil.copy2(str(source_mp3), str(dest))

        # ── 5. Embed ID3 metadata ────────────────────────────────────────────
        _tag_mp3(dest, title, artist, album, tmp, thumbnail_url)

        return dest.name


def _tag_mp3(
    path: Path,
    title: str,
    artist: str,
    album: str,
    tmpdir: Path,
    thumbnail_url: Optional[str],
) -> None:
    """Write ID3 tags (title, artist, album, cover art) to *path*."""
    try:
        audio = MP3(str(path), ID3=ID3)
    except Exception:
        audio = MP3(str(path))
        audio.add_tags()

    if audio.tags is None:
        audio.add_tags()

    audio.tags["TIT2"] = TIT2(encoding=3, text=title)
    audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
    audio.tags["TALB"] = TALB(encoding=3, text=album)

    # Try embedded thumbnail first, then remote URL
    cover_data = _find_cover(tmpdir, thumbnail_url)
    if cover_data:
        mime, data = cover_data
        audio.tags["APIC"] = APIC(
            encoding=0,
            mime=mime,
            type=3,
            desc="Cover",
            data=data,
        )

    audio.save()


def _find_cover(
    tmpdir: Path, thumbnail_url: Optional[str]
) -> Optional[tuple[str, bytes]]:
    """Return (mime_type, bytes) for a cover image, or None."""
    for ext, mime in [("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png"), ("webp", "image/webp")]:
        files = list(tmpdir.glob(f"*.{ext}"))
        if files:
            return mime, files[0].read_bytes()

    if thumbnail_url:
        try:
            resp = requests.get(thumbnail_url, timeout=10)
            if resp.ok:
                ct = resp.headers.get("content-type", "image/jpeg")
                mime = ct.split(";")[0].strip()
                return mime, resp.content
        except Exception:
            pass

    return None
