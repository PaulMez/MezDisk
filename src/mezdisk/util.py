from __future__ import annotations

from dataclasses import dataclass

from rich.filesize import decimal


def format_bytes(size_bytes: int) -> str:
    return decimal(size_bytes)


@dataclass(frozen=True, slots=True)
class Palette:
    dir_color: str = "bright_blue"
    error_color: str = "bright_red"
    label_dim: str = "dim"
