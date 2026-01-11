# AGENTS.md (MezDisk)

Guidance for agentic coding assistants working in this repo.

## 0) Existing assistant rules

- Cursor rules: **not present** (no `.cursor/rules/` or `.cursorrules` found).
- Copilot rules: **not present** (no `.github/copilot-instructions.md` found).

If any of these are added later, mirror their requirements here.

## 1) Project intent

MezDisk is a WinDirStat-like disk usage viewer for the terminal.

- Tech: **Python** + **Rich** (and `typer` for CLI).
- Core: fast directory scanning + size aggregation.
- UI: tree view + treemap-like blocks + “largest items” summary.

## 2) Tooling & commands (source of truth: `pyproject.toml`)

This repo uses a modern `src/` layout. Dependency management is designed for `uv`,
but `venv` + `pip` also works via `requirements*.txt`.

### Setup

- Preferred (if `uv` is installed): `uv sync`
- Fallback (venv + pip):
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `python -m pip install -r requirements-dev.txt`
  - Optional editable install: `python -m pip install -e .`

### Run

- If using `uv`:
  - `uv run mezdisk --help`
  - `uv run python -m mezdisk --help`
- If using venv + pip (after `pip install -e .`):
  - `mezdisk --help`
  - `python -m mezdisk --help`

### Lint / format

- Lint: `ruff check .`
- Format: `ruff format .`

### Tests

- Run all tests: `pytest`

**Run a single test (important)**

- Single file: `pytest tests/test_scan.py`
- Single test function: `pytest tests/test_scan.py -k test_scan_path_sums_file_sizes`
- Single node id: `pytest tests/test_scan.py::test_scan_depth_limit`
- Re-run failing tests: `pytest --lf`
- Stop on first failure: `pytest -x`

Notes:
- Tests import via `tests/conftest.py` adding `src/` to `sys.path`.

## 3) Repository layout

- `src/mezdisk/` package
  - `cli.py`: Typer entrypoint
  - `scan.py`: filesystem scanner (fast, resilient)
  - `render.py`: Rich UI composition
  - `treemap.py`: treemap layout + renderer
- `tests/`: pytest tests

Keep scanning logic independent from rendering.

## 4) Coding guidelines

### Formatting

- Use `ruff format` (configured in `pyproject.toml`).
- Target line length ~100; let the formatter decide.

### Imports

- Prefer absolute imports within the package: `from mezdisk.scan import ...`.
- Group imports: stdlib, third-party, local (ruff enforces this).
- Avoid wildcard imports.

### Types

- Add type hints for public APIs and non-trivial internals.
- Prefer `pathlib.Path` for paths.
- Prefer `list[str]`, `dict[str, int]`, etc. (Py3.10+).
- Avoid `Any` unless there is no reasonable alternative.

### Naming

- Files/modules: `snake_case.py`.
- Functions/variables: `snake_case`.
- Classes: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.

### Error handling & UX

- Validate external input at boundaries (CLI args, filesystem).
- Do not crash on a single unreadable directory:
  - catch narrow exceptions (`PermissionError`, `FileNotFoundError`, `OSError`)
  - attach context (e.g., store an error string on a node)
- Avoid bare `except:`.
- Keep user-facing output in the UI/CLI layer; deep helpers should not `print()`.

### Performance considerations

- Prefer `os.scandir()` over `os.walk()` for scanning.
- Be careful with symlinks (`--follow-symlinks` can loop).
- Throttle UI updates during scanning to avoid slowing traversal.

## 5) Git hygiene

- Keep changes minimal and scoped to the task.
- Do not reformat unrelated files.
- Do not commit generated artifacts (`.venv/`, caches, `dist/`, etc.).
