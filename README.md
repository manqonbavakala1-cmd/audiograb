# AudioGrab

A robust CLI music/audio downloader. Downloads audio from supported platforms (primarily YouTube), converts to high-quality MP3 (320kbps), and embeds ID3 metadata (Title, Artist, Album, Cover Art, Track Number).

## Setup

1. Python 3.13+ required.
2. Install ffmpeg and ensure it is on PATH.
3. Create virtual environment and install dependencies:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Download a URL:
```
python main.py "https://youtube.com/watch?v=..."
```

Search by name:
```
python main.py --search "Song Name"
```

Custom output dir and cookies:
```
python main.py "https://youtube.com/watch?v=..." -o "C:\Music" --cookies cookies.txt
```

Playlist URLs are supported; each track is tagged individually.
