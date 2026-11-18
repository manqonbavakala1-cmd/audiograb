from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import shutil
import yt_dlp
from pathlib import Path
from audiograb.tagger import tag
from audiograb.utils import sanitize_filename, ensure_dir

app = Flask(__name__)
DOWNLOADS_DIR = Path(__file__).parent / "downloads"
ensure_dir(DOWNLOADS_DIR)

# Find FFmpeg on both Windows and Linux
FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def handle_download():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "ffmpeg_location": FFMPEG_PATH,
            # 1. Add cookies back in (ensure cookies.txt exists in the root)
            "cookiefile": "cookies.txt",
            # 2. Force a specific YouTube client to bypass player errors
            "extractor_args": {"youtube": {"player_client": ["web", "tv"]}},
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Unknown Title")
            artist = info.get("uploader", "Unknown Artist")
            
            base = sanitize_filename(title)
            mp3_path = DOWNLOADS_DIR / f"{base}.mp3"
            
            if not mp3_path.exists():
                candidates = list(DOWNLOADS_DIR.glob("*.mp3"))
                if candidates:
                    mp3_path = max(candidates, key=lambda p: p.stat().st_mtime)

            thumb_path = None
            for ext in (".jpg", ".webp", ".png"):
                cand = DOWNLOADS_DIR / f"{base}{ext}"
                if cand.exists():
                    thumb_path = cand
                    break

        try:
            tag(str(mp3_path), title, artist, str(thumb_path) if thumb_path else None)
        except Exception as tag_error:
            print(f"Tagging failed: {tag_error}")
        
        return jsonify({
            "success": True,
            "title": title,
            "artist": artist,
            "filename": mp3_path.name
        })

    except Exception as e:
        print(f"DOWNLOAD ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/downloads/<filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
