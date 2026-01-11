from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text


@dataclass(frozen=True, slots=True)
class TreemapItem:
    label: str
    value: float
    color: str


@dataclass(frozen=True, slots=True)
class Rect:
    x: int
    y: int
    w: int
    h: int


def _normalize(values: list[float], area: float) -> list[float]:
    total = sum(values)
    if total <= 0:
        return [0.0 for _ in values]
    return [v * area / total for v in values]


def _worst_ratio(row: list[float], short_side: float) -> float:
    if not row or short_side <= 0:
        return float("inf")
    s = sum(row)
    m = max(row)
    n = min(row)
    if n <= 0:
        return float("inf")
    return max((short_side * short_side * m) / (s * s), (s * s) / (short_side * short_side * n))


def _layout_row(row: list[float], rect: Rect, horizontal: bool) -> tuple[list[Rect], Rect]:
    s = sum(row)
    if horizontal:
        h = max(1, int(round(s / rect.w)))
        y = rect.y
        x = rect.x
        out: list[Rect] = []
        for v in row:
            w = max(1, int(round(v / h)))
            out.append(Rect(x=x, y=y, w=w, h=h))
            x += w
        remaining = Rect(x=rect.x, y=rect.y + h, w=rect.w, h=max(0, rect.h - h))
        return out, remaining

    w = max(1, int(round(s / rect.h)))
    x = rect.x
    y = rect.y
    out = []
    for v in row:
        h = max(1, int(round(v / w)))
        out.append(Rect(x=x, y=y, w=w, h=h))
        y += h
    remaining = Rect(x=rect.x + w, y=rect.y, w=max(0, rect.w - w), h=rect.h)
    return out, remaining


def squarify(values: list[float], width: int, height: int) -> list[Rect]:
    if width <= 0 or height <= 0:
        return []

    normalized = _normalize(values, float(width * height))
    normalized = [v for v in normalized if v > 0]
    if not normalized:
        return []

    rect = Rect(x=0, y=0, w=width, h=height)
    row: list[float] = []
    out: list[Rect] = []

    remaining_values = normalized[:]
    while remaining_values and rect.w > 0 and rect.h > 0:
        v = remaining_values[0]
        short_side = float(min(rect.w, rect.h))
        if not row:
            row.append(v)
            remaining_values.pop(0)
            continue

        current = _worst_ratio(row, short_side)
        candidate = _worst_ratio(row + [v], short_side)
        if candidate <= current:
            row.append(v)
            remaining_values.pop(0)
            continue

        horizontal = rect.w >= rect.h
        placed, rect = _layout_row(row, rect, horizontal)
        out.extend(placed)
        row = []

    if row and rect.w > 0 and rect.h > 0:
        horizontal = rect.w >= rect.h
        placed, rect = _layout_row(row, rect, horizontal)
        out.extend(placed)

    return out


class Treemap:
    def __init__(self, items: Iterable[TreemapItem], *, height: int = 16) -> None:
        self._items = list(items)
        self._height = height

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        width = max(1, options.max_width)
        height = max(1, min(self._height, options.max_height or self._height))

        if not self._items:
            yield Text("(no data)", style="dim")
            return

        values = [max(0.0, i.value) for i in self._items]
        rects = squarify(values, width, height)
        count = min(len(rects), len(self._items))

        grid: list[list[int]] = [[-1 for _ in range(width)] for _ in range(height)]
        for idx in range(count):
            r = rects[idx]
            x2 = min(width, r.x + r.w)
            y2 = min(height, r.y + r.h)
            for y in range(r.y, y2):
                row = grid[y]
                for x in range(r.x, x2):
                    row[x] = idx

        label_cells: list[tuple[int, int, str]] = []
        for idx in range(count):
            r = rects[idx]
            if r.w < 6 or r.h < 2:
                continue
            label = self._items[idx].label[: r.w - 1]
            label_cells.append((r.x + 1, r.y, label))

        labels_by_row: dict[int, list[tuple[int, str]]] = {}
        for x, y, label in label_cells:
            labels_by_row.setdefault(y, []).append((x, label))

        for y in range(height):
            text = Text()
            labels = sorted(labels_by_row.get(y, []), key=lambda t: t[0])
            label_idx = 0
            x = 0
            while x < width:
                if label_idx < len(labels) and x == labels[label_idx][0]:
                    label = labels[label_idx][1]
                    text.append(label, style="bold white")
                    x += len(label)
                    label_idx += 1
                    continue

                item_idx = grid[y][x]
                if item_idx == -1:
                    text.append(" ")
                else:
                    color = self._items[item_idx].color
                    text.append(" ", style=f"on {color}")
                x += 1

            yield text
