import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from audiograb.cli import build_parser
from audiograb.downloader import download, ffmpeg_available
from audiograb.tagger import tag
from audiograb.utils import ensure_dir

console = Console()

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    console.print(Panel.fit("[bold magenta]AudioGrab[/bold magenta] - music downloader", border_style="magenta"))

    # Check if our local ffmpeg folder exists
    if not ffmpeg_available():
        console.print("[bold red]ERROR: ffmpeg not found![/bold red] Please ensure the 'ffmpeg' folder is inside your AudioGrab directory.")
        return 1

    source = args.search if args.search else args.url
    if not source:
        console.print("[red]Error: provide a URL or --search query.[/red]")
        return 1

    out_dir = Path(args.output)
    try:
        ensure_dir(out_dir)
    except OSError as e:
        console.print(f"[red]Error: cannot create output directory {out_dir}: {e}[/red]")
        return 1

    query = f"ytsearch1:{args.search}" if args.search else source

    console.print(f"[cyan]Downloading:[/cyan] {query}")
    
    try:
        results = download(query, out_dir, args.quality, getattr(args, "cookies", None))
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        return 130
    except Exception as e:
        console.print(f"[red]Error during download: {e}[/red]")
        return 1

    for result in results:
        try:
            tag(result["file_path"], result["title"], result["artist"], result["thumbnail_path"], track=result.get("track"))
        except Exception as e:
            console.print(f"[yellow]Warning: tagging failed: {e}[/yellow]")
        console.print(f"[green]✔ Done:[/green] {result['title']} - {result['artist']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())