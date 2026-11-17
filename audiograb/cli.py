"""CLI for AudioGrab."""
import argparse
import glob
import sys
from pathlib import Path

from .downloader import download, ffmpeg_available
from .tagger import tag
from .utils import ensure_dir

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="audiograb", description="AudioGrab - music downloader")
    p.add_argument("url", nargs="?", help="URL to download")
    p.add_argument("--search", "-s", help="Search query instead of URL")
    p.add_argument("-o", "--output", default="downloads", help="Output directory")
    p.add_argument("-q", "--quality", default="320", help="MP3 bitrate (kbps)")
    p.add_argument("--cookies", help="Path to cookies.txt file")
    return p

def cleanup_parts(out_dir):
    for f in glob.glob(str(Path(out_dir) / "*.part")):
        try:
            Path(f).unlink()
        except OSError:
            pass

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if not ffmpeg_available():
        print("WARNING: ffmpeg not found in the 'ffmpeg/bin' folder or on PATH.")

    source = args.search if args.search else args.url
    if not source:
        print("Error: provide a URL or --search query.")
        return 1

    out_dir = Path(args.output)
    try:
        ensure_dir(out_dir)
    except OSError as e:
        print(f"Error: cannot create output directory {out_dir}: {e}")
        return 1

    query = f"ytsearch1:{args.search}" if args.search else source

    print(f"Downloading from: {source}")
    try:
        results = download(query, out_dir, args.quality, getattr(args, "cookies", None))
    except KeyboardInterrupt:
        cleanup_parts(out_dir)
        print("\nCancelled by user. Cleaned up partial files.")
        return 130
    except Exception as e:
        print(f"Error during download: {e}")
        return 1

    for result in results:
        file_path = result["file_path"]
        title = result["title"]
        artist = result["artist"]
        cover = result["thumbnail_path"]
        track = result.get("track")

        print(f"Downloaded: {file_path}")
        print("Embedding ID3 tags...")
        try:
            tag(file_path, title, artist, cover, track=track)
            print("Tags embedded successfully.")
        except Exception as e:
            print(f"Warning: tagging failed: {e}")

        print(f"Done: {title} - {artist}")

    return 0

if __name__ == "__main__":
    sys.exit(main())