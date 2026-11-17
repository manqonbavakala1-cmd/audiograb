"""yt-dlp based downloader for AudioGrab."""
import re
import shutil
from pathlib import Path

import yt_dlp

from .utils import ensure_dir, sanitize_filename

# ABSOLUTE PATH to where your ffmpeg.exe actually lives
FFMPEG_FOLDER = r"C:\Users\223074993\Desktop\AudioGrab\ffmpeg\bin"

def ffmpeg_available() -> bool:
    if Path(FFMPEG_FOLDER, "ffmpeg.exe").exists():
        return True
    return shutil.which("ffmpeg") is not None

def download(url_or_query: str, output_dir, quality: str = "320", cookiefile=None, progress_callback=None) -> list:
    out_dir = ensure_dir(output_dir)
    results = []

    def hook(d):
        if progress_callback and d.get("status") == "downloading":
            pct = d.get("_percent_str", "0%").replace("%", "").strip()
            try:
                progress_callback(float(pct))
            except:
                pass

    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "writethumbnail": True,
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": FFMPEG_FOLDER,
        "progress_hooks": [hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url_or_query, download=True)

    entries = info.get("entries") if isinstance(info, dict) else None
    if not entries:
        entries = [info]

    for entry in entries:
        if entry is None: continue
        title = entry.get("title") or "Unknown Title"
        artist = entry.get("uploader") or entry.get("channel") or "Unknown Artist"
        base = sanitize_filename(title)
        mp3_path = out_dir / f"{base}.mp3"
        
        if not mp3_path.exists():
            candidates = list(out_dir.glob("*.mp3"))
            if candidates:
                mp3_path = max(candidates, key=lambda p: p.stat().st_mtime)

        thumb_path = None
        for ext in (".jpg", ".webp", ".png"):
            cand = out_dir / f"{base}{ext}"
            if cand.exists():
                thumb_path = cand
                break

        results.append({
            "file_path": str(mp3_path),
            "title": title,
            "artist": artist,
            "thumbnail_path": str(thumb_path) if thumb_path else None,
            "track": entry.get("playlist_index"),
        })

    return results
