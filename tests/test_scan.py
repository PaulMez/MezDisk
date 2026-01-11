from __future__ import annotations

from pathlib import Path

from mezdisk.scan import ScanConfig, scan_path


def test_scan_path_sums_file_sizes(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"a" * 10)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"b" * 25)

    result = scan_path(tmp_path, ScanConfig(max_depth=None, follow_symlinks=False))

    assert result.root.is_dir
    assert result.root.size_bytes == 35
    assert result.stats.files >= 2
    assert result.stats.dirs >= 2


def test_scan_depth_limit(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.txt").write_bytes(b"x" * 100)

    result = scan_path(tmp_path, ScanConfig(max_depth=0, follow_symlinks=False))

    # Depth 0 means: scan root directory entries are not traversed.
    assert result.root.is_dir
    assert result.root.size_bytes == 0
