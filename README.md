# MezDisk

WinDirStat-like disk usage viewer for the terminal.

MezDisk scans a path, aggregates sizes, and renders a visual overview:

- Tree view (size-sorted)
- Treemap-like blocks (colored by file type)
- “Largest items” table

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

### Interactive (Textual UI) (default)

```bash
mezdisk .
mezdisk /some/path
```

- Quit: press `q`
- Select a directory/file in the tree to update the treemap + largest table.

### Rich report (non-interactive)

```bash
mezdisk . --ui rich
```

### Useful options

```bash
mezdisk . --max-depth 4
mezdisk . --follow-symlinks
mezdisk . --tree-depth 5 --treemap-items 40 --treemap-height 22
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
