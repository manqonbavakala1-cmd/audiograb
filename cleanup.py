"""Cleanup script to remove old downloads."""
import time
from pathlib import Path

DOWNLOADS_DIR = Path(__file__).parent / "downloads"
MAX_AGE_SECONDS = 15 * 60


def cleanup():
    if not DOWNLOADS_DIR.exists():
        return
    now = time.time()
    for f in DOWNLOADS_DIR.iterdir():
        try:
            if f.is_file() and now - f.stat().st_mtime > MAX_AGE_SECONDS:
                f.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    cleanup()
    print("Cleanup complete.")
