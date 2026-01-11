from __future__ import annotations

import time
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .render import RenderConfig, build_report
from .scan import ScanConfig, scan_path
from .tui import MezDiskApp, TuiConfig

app = typer.Typer(add_completion=False, no_args_is_help=True)


class UiMode(str, Enum):
    textual = "textual"
    rich = "rich"


@app.command()
def main(
    path: Path = typer.Argument(Path("."), help="Path to scan (file or directory)."),
    ui: UiMode = typer.Option(UiMode.textual, help="UI mode: textual (interactive) or rich."),
    max_depth: int | None = typer.Option(
        None, help="Max scan depth (None = full scan). Lower is faster."
    ),
    tree_depth: int = typer.Option(4, help="Depth shown in the Rich tree panel."),
    follow_symlinks: bool = typer.Option(False, help="Follow symlinks (can loop)."),
    treemap_height: int = typer.Option(18, help="Height of treemap panel in rows."),
    treemap_items: int = typer.Option(25, help="Number of items in treemap."),
) -> None:
    """Scan disk usage and render a WinDirStat-ish UI."""

    console = Console()
    root_path = path.expanduser().resolve()

    last_update = 0.0

    def on_visit(p: Path) -> None:
        nonlocal last_update
        now = time.monotonic()
        if now - last_update < 0.05:
            return
        last_update = now
        progress.update(task_id, description=f"Scanning: {p}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task("Starting...", total=None)
        result = scan_path(
            root_path,
            ScanConfig(max_depth=max_depth, follow_symlinks=follow_symlinks, on_visit=on_visit),
        )

    if ui == UiMode.textual:
        MezDiskApp(
            result=result,
            root_path=root_path,
            config=TuiConfig(treemap_height=treemap_height, treemap_items=treemap_items),
        ).run()
        return

    config = RenderConfig(
        tree_depth=tree_depth,
        treemap_height=treemap_height,
        treemap_items=treemap_items,
    )

    console.print(build_report(result, root_path=root_path, config=config))


if __name__ == "__main__":
    app()
