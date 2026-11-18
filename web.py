from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import shutil
import time
import yt_dlp
from pathlib import Path
from audiograb.tagger import tag
from audiograb.utils import sanitize_filename, ensure_dir

# Rate Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

DOWNLOADS_DIR = Path(__file__).parent / "downloads"
ensure_dir(DOWNLOADS_DIR)
FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"

# --- AUTO CLEANUP FUNCTION ---
def cleanup_old_files():
    """Deletes files older than 15 minutes to save space."""
    now = time.time()
    for f in DOWNLOADS_DIR.glob("*"):
        if f.is_file() and now - f.stat().st_mtime > 900: # 900 seconds = 15 mins
            try:
                f.unlink()
            except:
                pass

@app.route('/')
def index():
    cleanup_old_files() # Run cleanup every time the page loads
    return render_template('index.html')

@app.route('/download', methods=['POST'])
@limiter.limit("5 per minute") # Prevents bots from spamming
def handle_download():
    url = request.form.get('url')
    format_choice = request.form.get('format', 'mp3_320') # Default to 320

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Map the dropdown choices to yt-dlp settings
    if format_choice == 'mp3_128':
        codec, quality = "mp3", "128"
    elif format_choice == 'm4a':
        codec, quality = "m4a", "192"
    elif format_choice == 'wav':
        codec, quality = "wav", "0"
    else:
        codec, quality = "mp3", "320"

    try:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "ffmpeg_location": FFMPEG_PATH,
            "cookiefile": "cookies.txt",
            # Removed extractor_args to fix format availability
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
                "preferredquality": quality,
            }],
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Unknown Title")
            artist = info.get("uploader", "Unknown Artist")
            
            base = sanitize_filename(title)
            media_path = DOWNLOADS_DIR / f"{base}.{codec}"
            
            if not media_path.exists():
                candidates = list(DOWNLOADS_DIR.glob(f"*.{codec}"))
                if candidates:
                    media_path = max(candidates, key=lambda p: p.stat().st_mtime)

            thumb_path = None
            for ext in (".jpg", ".webp", ".png"):
                cand = DOWNLOADS_DIR / f"{base}{ext}"
                if cand.exists():
                    thumb_path = cand
                    break

        if codec in ["mp3", "m4a"]:
            try:
                tag(str(media_path), title, artist, str(thumb_path) if thumb_path else None)
            except Exception as tag_error:
                print(f"Tagging failed: {tag_error}")
        
        return jsonify({
            "success": True,
            "title": title,
            "artist": artist,
            "filename": media_path.name
        })

    except Exception as e:
        print(f"DOWNLOAD ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/downloads/<filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
