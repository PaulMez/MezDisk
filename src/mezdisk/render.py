from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.align import Align
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from .filetypes import file_style
from .models import Node, ScanResult
from .treemap import Treemap, TreemapItem
from .util import Palette, format_bytes


@dataclass(frozen=True, slots=True)
class RenderConfig:
    tree_depth: int = 4
    max_children: int = 30
    treemap_height: int = 18
    treemap_items: int = 25


def build_report(result: ScanResult, root_path: Path, config: RenderConfig) -> Layout:
    palette = Palette()

    header = Panel(
        Group(
            Text("MezDisk", style="bold"),
            Text(
                f"Path: {root_path}   Total: {format_bytes(result.root.size_bytes)}   "
                f"Dirs: {result.stats.dirs}   Files: {result.stats.files}   "
                f"Errors: {result.stats.errors}   Time: {result.elapsed_s:.2f}s",
                style=palette.label_dim,
            ),
        ),
        border_style="bright_blue",
    )

    tree = build_tree(result.root, total=result.root.size_bytes, max_depth=config.tree_depth)
    tree_panel = Panel(tree, title="Tree", border_style="bright_blue")

    treemap_items = build_treemap_items(result.root, max_items=config.treemap_items)
    treemap = Treemap(treemap_items, height=config.treemap_height)
    treemap_panel = Panel(treemap, title="Treemap", border_style="bright_blue")

    top_table = build_top_table(result.root, total=result.root.size_bytes, max_rows=12)
    footer = Panel(Align.left(top_table), title="Largest", border_style="bright_blue")

    layout = Layout(name="root")
    layout.split_column(
        Layout(header, name="header", size=4),
        Layout(name="body", ratio=1),
        Layout(footer, name="footer", size=14),
    )

    layout["body"].split_row(
        Layout(tree_panel, name="left", ratio=1),
        Layout(treemap_panel, name="right", ratio=2),
    )

    return layout


def build_tree(node: Node, *, total: int, max_depth: int) -> Tree:
    palette = Palette()

    def label(n: Node) -> Text:
        size = format_bytes(n.size_bytes)
        percent = ""
        if total > 0:
            percent = f"  ({(n.size_bytes / total) * 100:4.1f}%)"

        if n.is_dir:
            style = palette.dir_color
        else:
            style = file_style(n.path).color

        base = Text(f"{n.name} ", style=style)
        base.append(f"{size}{percent}", style="dim")
        if n.error:
            base.append(f"  ! {n.error}", style=palette.error_color)
        return base

    root = Tree(label(node), guide_style="dim")

    def add_children(parent: Tree, n: Node, depth: int) -> None:
        if depth >= max_depth:
            return
        if not n.children:
            return

        children = sorted(n.children, key=lambda c: c.size_bytes, reverse=True)
        for child in children:
            branch = parent.add(label(child))
            if child.is_dir:
                add_children(branch, child, depth + 1)

    add_children(root, node, 0)
    return root


def build_treemap_items(node: Node, *, max_items: int) -> list[TreemapItem]:
    palette = Palette()
    if not node.children:
        return []

    children = sorted(node.children, key=lambda c: c.size_bytes, reverse=True)
    if len(children) <= max_items:
        selected = children
        remainder: list[Node] = []
    else:
        selected = children[:max_items]
        remainder = children[max_items:]

    items: list[TreemapItem] = []
    for child in selected:
        color = palette.dir_color if child.is_dir else file_style(child.path).color
        items.append(TreemapItem(label=child.name, value=float(child.size_bytes), color=color))

    other_size = sum(c.size_bytes for c in remainder)
    if other_size > 0:
        items.append(TreemapItem(label="Other", value=float(other_size), color="grey37"))

    return items


def build_top_table(node: Node, *, total: int, max_rows: int) -> Table:
    rows = []

    def collect(n: Node) -> None:
        for child in n.children:
            rows.append(child)
            if child.is_dir:
                collect(child)

    collect(node)
    rows.sort(key=lambda c: c.size_bytes, reverse=True)
    rows = rows[:max_rows]

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Path", overflow="fold")
    table.add_column("Size", justify="right")
    table.add_column("%", justify="right")

    for item in rows:
        pct = 0.0 if total <= 0 else (item.size_bytes / total) * 100
        name = str(item.path)
        table.add_row(name, format_bytes(item.size_bytes), f"{pct:4.1f}")

    return table
