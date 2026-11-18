
opts = {
    "format": "bestaudio/best",
    "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
    "writethumbnail": True,
    "quiet": True,
    "no_warnings": True,
    "ffmpeg_location": FFMPEG_PATH,
