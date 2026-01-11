from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Node:
    path: Path
    is_dir: bool
    size_bytes: int = 0
    children: list["Node"] = field(default_factory=list)
    error: str | None = None

    @property
    def name(self) -> str:
        if self.path.name:
            return self.path.name
        return str(self.path)


@dataclass(frozen=True, slots=True)
class ScanStats:
    files: int
    dirs: int
    errors: int


@dataclass(frozen=True, slots=True)
class ScanResult:
    root: Node
    stats: ScanStats
    elapsed_s: float
