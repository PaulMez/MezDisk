# MezDisk

WinDirStat-like disk usage viewer for the terminal.

This `main` branch currently ships a Rich-based (non-interactive) report:

- Tree view (size-sorted)
- Treemap-like blocks (colored by file type)
- “Largest items” table

If you want an interactive UI (keyboard-driven panes), see branch `textual-mvp`.

## Install

### Option A: `uv` (fast, recommended)

```bash
uv sync
```

### Option B: `venv` + `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## Run

```bash
mezdisk .
mezdisk /some/path --max-depth 4
mezdisk /some/path --follow-symlinks
mezdisk /some/path --tree-depth 5 --treemap-items 40 --treemap-height 22
```

## Develop

```bash
ruff check .
ruff format .
pytest
```

Single test examples:

```bash
pytest tests/test_scan.py
pytest tests/test_scan.py -k test_scan_depth_limit
pytest tests/test_scan.py::test_scan_path_sums_file_sizes
```

## Notes

- `--follow-symlinks` can loop on cyclic links.
- Permission errors are captured and shown inline instead of crashing.
