"""ID3 tagging with iTunes metadata lookup for AudioGrab."""
import re
from pathlib import Path

import requests
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, TRCK
from mutagen.mp3 import MP3

from .utils import cleanup

def clean_title(title: str) -> str:
    title = re.sub(r"\(Official.*?\)", "", title, flags=re.I)
    title = re.sub(r"\[.*?\]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def fetch_itunes_metadata(title: str, artist: str):
    query = f"{title} {artist}".strip()
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "media": "music", "limit": 1},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("resultCount", 0) > 0:
            res = data["results"][0]
            art_url = res.get("artworkUrl100", "").replace("100x100", "600x600")
            return {
                "title": res.get("trackName", title),
                "artist": res.get("artistName", artist),
                "album": res.get("collectionName", "AudioGrab"),
                "cover_url": art_url,
            }
    except Exception:
        pass
    return {"title": title, "artist": artist, "album": "AudioGrab", "cover_url": None}

def tag(file_path: str, title: str, artist: str, cover_path: str = None, album: str = "AudioGrab", track=None) -> None:
    title = clean_title(title)
    meta = fetch_itunes_metadata(title, artist)
    title = meta["title"]
    artist = meta["artist"]
    album = meta["album"]

    path = Path(file_path)
    audio = MP3(str(path))
    if audio.tags is None:
        audio.add_tags()
    tags = audio.tags
    tags["TIT2"] = TIT2(encoding=3, text=title)
    tags["TPE1"] = TPE1(encoding=3, text=artist)
    tags["TALB"] = TALB(encoding=3, text=album)
    if track is not None:
        tags["TRCK"] = TRCK(encoding=3, text=str(track))

    cover_data = None
    if meta.get("cover_url"):
        try:
            resp = requests.get(meta["cover_url"], timeout=15)
            resp.raise_for_status()
            cover_data = resp.content
        except Exception:
            pass

    # --- CRITICAL FIX: Check if cover_path exists before reading it ---
    if cover_data is None and cover_path and Path(cover_path).exists():
        cover_data = Path(cover_path).read_bytes()

    if cover_data:
        tags["APIC"] = APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=cover_data,
        )

    # --- CRITICAL FIX: Only cleanup if cover_path is not None ---
    if cover_path:
        cleanup(cover_path)

    audio.save()
    print(f"Tagged: {title} - {artist} ({album})")