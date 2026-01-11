from __future__ import annotations

import heapq
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import count

from rich.filesize import decimal

from .models import Node


def format_bytes(size_bytes: int) -> str:
    return decimal(size_bytes)


def iter_leaf_files(node: Node) -> Iterator[Node]:
    stack = [node]
    while stack:
        current = stack.pop()
        if current.is_dir:
            stack.extend(reversed(current.children))
            continue
        yield current


def largest_leaf_files(node: Node, *, max_items: int) -> tuple[list[Node], int]:
    """Return the largest leaf files beneath `node`.

    Returns (selected_files, other_size_bytes) where `other_size_bytes` is the total
    size of files that did not make it into the `selected_files` list.
    """

    total_size = 0
    if max_items <= 0:
        for f in iter_leaf_files(node):
            total_size += max(0, f.size_bytes)
        return [], total_size

    heap: list[tuple[int, int, Node]] = []
    counter = count()

    for f in iter_leaf_files(node):
        size = max(0, f.size_bytes)
        total_size += size

        item = (size, next(counter), f)
        if len(heap) < max_items:
            heapq.heappush(heap, item)
            continue

        if size > heap[0][0]:
            heapq.heapreplace(heap, item)

    selected_sorted = sorted(heap, key=lambda t: t[0], reverse=True)
    selected_files = [t[2] for t in selected_sorted]
    selected_total = sum(t[0] for t in heap)

    other_size = max(0, total_size - selected_total)
    return selected_files, other_size


@dataclass(frozen=True, slots=True)
class Palette:
    dir_color: str = "bright_blue"
    error_color: str = "bright_red"
    label_dim: str = "dim"
