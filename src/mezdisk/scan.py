from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .models import Node, ScanResult, ScanStats


@dataclass(frozen=True, slots=True)
class ScanConfig:
    max_depth: int | None = None
    follow_symlinks: bool = False
    on_visit: Callable[[Path], None] | None = None


def scan_path(path: Path, config: ScanConfig) -> ScanResult:
    start = time.perf_counter()
    files = 0
    dirs = 0
    errors = 0

    def walk_dir(current: Path, depth: int) -> Node:
        nonlocal files, dirs, errors

        node = Node(path=current, is_dir=True)
        dirs += 1

        if config.max_depth is not None and depth >= config.max_depth:
            return node

        total = 0
        try:
            with os.scandir(current) as it:
                for entry in it:
                    child = walk_entry(entry, depth + 1)
                    node.children.append(child)
                    total += child.size_bytes
        except (PermissionError, FileNotFoundError, NotADirectoryError, OSError) as exc:
            node.error = f"{type(exc).__name__}: {exc}"
            errors += 1

        node.size_bytes = total
        return node

    def walk_file(current: Path) -> Node:
        nonlocal files, errors

        files += 1
        try:
            stat = current.stat(follow_symlinks=config.follow_symlinks)
            return Node(path=current, is_dir=False, size_bytes=stat.st_size)
        except (PermissionError, FileNotFoundError, OSError) as exc:
            errors += 1
            return Node(path=current, is_dir=False, size_bytes=0, error=f"{type(exc).__name__}: {exc}")

    def walk_entry(entry: os.DirEntry[str], depth: int) -> Node:
        nonlocal files, errors

        child_path = Path(entry.path)
        if config.on_visit is not None:
            config.on_visit(child_path)

        try:
            if entry.is_symlink() and not config.follow_symlinks:
                files += 1
                return Node(path=child_path, is_dir=False, size_bytes=0)

            if entry.is_dir(follow_symlinks=config.follow_symlinks):
                return walk_dir(child_path, depth)

            files += 1
            stat = entry.stat(follow_symlinks=config.follow_symlinks)
            return Node(path=child_path, is_dir=False, size_bytes=stat.st_size)
        except (PermissionError, FileNotFoundError, OSError) as exc:
            errors += 1
            return Node(path=child_path, is_dir=False, size_bytes=0, error=f"{type(exc).__name__}: {exc}")

    if config.on_visit is not None:
        config.on_visit(path)

    try:
        if path.is_symlink() and not config.follow_symlinks:
            files += 1
            root = Node(path=path, is_dir=False, size_bytes=0)
        elif path.is_dir():
            root = walk_dir(path, 0)
        else:
            root = walk_file(path)
    except (PermissionError, FileNotFoundError, OSError) as exc:
        errors += 1
        root = Node(path=path, is_dir=False, size_bytes=0, error=f"{type(exc).__name__}: {exc}")

    elapsed = time.perf_counter() - start
    return ScanResult(root=root, stats=ScanStats(files=files, dirs=dirs, errors=errors), elapsed_s=elapsed)

