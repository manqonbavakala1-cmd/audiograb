"""Helper utilities for AudioGrab."""
import re
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Remove characters illegal in Windows filenames."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or "untitled"


def ensure_dir(path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def cleanup(path) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
