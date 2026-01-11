from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileTypeStyle:
    label: str
    color: str


_FILETYPE_STYLES: list[tuple[set[str], FileTypeStyle]] = [
    (
        {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"},
        FileTypeStyle("archive", "magenta"),
    ),
    (
        {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"},
        FileTypeStyle("image", "bright_cyan"),
    ),
    (
        {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
        FileTypeStyle("audio", "bright_green"),
    ),
    (
        {".mp4", ".mkv", ".mov", ".avi", ".webm"},
        FileTypeStyle("video", "bright_yellow"),
    ),
    (
        {".py", ".rs", ".go", ".js", ".ts", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp"},
        FileTypeStyle("code", "blue"),
    ),
    (
        {".md", ".txt", ".pdf", ".doc", ".docx", ".rtf"},
        FileTypeStyle("doc", "green"),
    ),
]


def file_style(path: Path) -> FileTypeStyle:
    suffix = path.suffix.lower()
    for extensions, style in _FILETYPE_STYLES:
        if suffix in extensions:
            return style
    return FileTypeStyle("other", "white")
