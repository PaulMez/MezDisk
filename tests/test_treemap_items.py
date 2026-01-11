from __future__ import annotations

from pathlib import Path

from mezdisk.render import build_treemap_items
from mezdisk.scan import ScanConfig, scan_path


def test_treemap_items_are_leaf_files_only(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"a" * 10)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"b" * 25)

    result = scan_path(tmp_path, ScanConfig(max_depth=None, follow_symlinks=False))

    items = build_treemap_items(result.root, max_items=1)
    assert [i.label for i in items] == ["sub/b.bin", "Other"]
    assert [i.value for i in items] == [25.0, 10.0]
