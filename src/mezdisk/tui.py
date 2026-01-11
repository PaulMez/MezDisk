from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.table import Table
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static, Tree

from .filetypes import file_style
from .models import Node, ScanResult
from .treemap import Treemap, TreemapItem
from .util import format_bytes, largest_leaf_files


@dataclass(frozen=True, slots=True)
class TuiConfig:
    treemap_height: int = 20
    treemap_items: int = 35
    largest_items: int = 20


class MezDiskApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
    }

    #left {
        width: 1fr;
        border: round $primary;
    }

    #right {
        width: 2fr;
        border: round $primary;
    }

    #bottom {
        height: 16;
        border: round $primary;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, *, result: ScanResult, root_path: Path, config: TuiConfig) -> None:
        super().__init__()
        self._result = result
        self._root_path = root_path
        self._config = config

        self._node_by_key: dict[str, Node] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            yield Tree("MezDisk", id="left")
            with Vertical(id="right"):
                yield Static(id="treemap")
        yield Static(id="bottom")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "MezDisk"
        self.sub_title = str(self._root_path)

        tree = self.query_one(Tree)
        tree.root.label = f"{self._root_path}  ({format_bytes(self._result.root.size_bytes)})"
        tree.root.data = str(self._root_path)
        self._node_by_key[str(self._root_path)] = self._result.root

        tree.root.expand()
        self._populate_tree(tree.root, self._result.root, max_depth=4)
        self._select_node(self._result.root)

    def _populate_tree(self, tree_node: Tree.Node, node: Node, *, max_depth: int) -> None:
        if max_depth <= 0:
            return

        children = sorted(node.children, key=lambda c: c.size_bytes, reverse=True)
        for child in children:
            key = str(child.path)
            label = f"{child.name}  {format_bytes(child.size_bytes)}"
            if child.is_dir:
                label = f"[bold]{label}[/]"
            else:
                label = f"[{file_style(child.path).color}]{label}[/]"
            if child.error:
                label += f"  [red]! {child.error}[/]"

            branch = tree_node.add(label, expand=False)
            branch.data = key
            self._node_by_key[key] = child

            if child.is_dir and child.children:
                # Add a placeholder so it looks expandable.
                branch.add("…", expand=False)

    def _ensure_children_loaded(self, tree_node: Tree.Node, node: Node) -> None:
        # Replace the placeholder child ("…") once.
        if not tree_node.children or len(tree_node.children) != 1:
            return

        if str(tree_node.children[0].label).strip() != "…":
            return

        # Textual exposes a helper for this; avoids poking internal lists.
        tree_node.remove_children()
        self._populate_tree(tree_node, node, max_depth=2)

    def _select_node(self, node: Node) -> None:
        self._render_treemap(node)
        self._render_largest_table(node)

    def _render_treemap(self, node: Node) -> None:
        widget = self.query_one("#treemap", Static)

        selected_files, other_size = largest_leaf_files(node, max_items=self._config.treemap_items)
        if not selected_files and other_size <= 0:
            widget.update("(no files)")
            return

        def label_for(f: Node) -> str:
            if node.is_dir:
                try:
                    return str(f.path.relative_to(node.path))
                except ValueError:
                    return str(f.path)
            return f.name

        items: list[TreemapItem] = []
        for f in selected_files:
            items.append(
                TreemapItem(
                    label=label_for(f), value=float(f.size_bytes), color=file_style(f.path).color
                )
            )

        if other_size > 0:
            items.append(TreemapItem(label="Other", value=float(other_size), color="grey37"))

        widget.update(Treemap(items, height=self._config.treemap_height))

    def _render_largest_table(self, node: Node) -> None:
        widget = self.query_one("#bottom", Static)

        total = max(0, node.size_bytes)
        items: list[Node] = []

        def collect(n: Node) -> None:
            for child in n.children:
                items.append(child)
                if child.is_dir:
                    collect(child)

        collect(node)
        items.sort(key=lambda n: n.size_bytes, reverse=True)
        items = items[: self._config.largest_items]

        table = Table(title="Largest", show_header=True, header_style="bold")
        table.add_column("Path", overflow="fold")
        table.add_column("Size", justify="right")
        table.add_column("%", justify="right")

        for item in items:
            pct = 0.0 if total <= 0 else (item.size_bytes / total) * 100
            table.add_row(str(item.path), format_bytes(item.size_bytes), f"{pct:4.1f}")

        widget.update(table)

    @on(Tree.NodeSelected)
    def _on_tree_selected(self, event: Tree.NodeSelected) -> None:
        key = event.node.data
        if not isinstance(key, str):
            return

        node = self._node_by_key.get(key)
        if node is None:
            return

        if node.is_dir:
            self._ensure_children_loaded(event.node, node)

        self._select_node(node)
