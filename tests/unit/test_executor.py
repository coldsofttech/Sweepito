from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from sweepito import executor
from sweepito.executor import apply_plan
from sweepito.models import Candidate, Plan, Risk


def candidate(path: str, is_dir: bool = False, size: int = 0) -> Candidate:
    return Candidate("r", "p", Risk.SAFE, path, is_dir, size)


def make_plan(root: Path, *candidates: Candidate) -> Plan:
    plan = Plan(root=root)
    plan.candidates.extend(candidates)
    return plan


def write(path: Path, content: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_removes_files_and_directory_trees(tmp_path: Path) -> None:
    write(tmp_path / "a.bin", "x" * 40)
    write(tmp_path / "build" / "one.o", "x" * 10)
    write(tmp_path / "build" / "deep" / "two.o", "x" * 20)
    plan = make_plan(tmp_path, candidate("a.bin"), candidate("build", is_dir=True))
    result = apply_plan(plan, in_git=False)
    assert [c.path for c in result.removed] == ["a.bin", "build"]
    assert not result.failed and not result.skipped
    assert result.freed_bytes == 70
    assert not (tmp_path / "a.bin").exists()
    assert not (tmp_path / "build").exists()


def test_a_path_that_is_already_gone_counts_as_removed(tmp_path: Path) -> None:
    result = apply_plan(make_plan(tmp_path, candidate("gone")), in_git=False)
    assert [c.path for c in result.removed] == ["gone"]
    assert result.freed_bytes == 0 and not result.failed


def test_never_cleans_inside_dot_git(tmp_path: Path) -> None:
    config = write(tmp_path / ".git" / "config")
    result = apply_plan(make_plan(tmp_path, candidate(".git/config")), in_git=False)
    assert [s.reason for s in result.skipped] == ["inside .git (never cleaned)"]
    assert config.exists() and not result.removed


def test_refuses_paths_that_resolve_outside_the_root(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    outside = write(tmp_path / "outside.txt")
    result = apply_plan(make_plan(root, candidate("../outside.txt")), in_git=False)
    assert [s.reason for s in result.skipped] == ["resolves outside the project root"]
    assert outside.exists()


def test_tracked_paths_are_skipped_when_in_git(tmp_path: Path) -> None:
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    tracked = write(tmp_path / "src" / "keep.py")
    loose = write(tmp_path / "loose.tmp")
    subprocess.run(["git", "-C", str(tmp_path), "add", "src"], check=True)
    plan = make_plan(
        tmp_path,
        candidate("src/keep.py"),
        candidate("src", is_dir=True),
        candidate("loose.tmp"),
    )
    result = apply_plan(plan)
    assert [s.reason for s in result.skipped] == ["tracked by git"] * 2
    assert [c.path for c in result.removed] == ["loose.tmp"]
    assert tracked.exists() and not loose.exists()


def test_symlinks_are_removed_as_links_not_followed(tmp_path: Path) -> None:
    target = tmp_path / "target"
    keep = write(target / "keep.txt")
    build = tmp_path / "build"
    build.mkdir()
    try:
        os.symlink(target, build / "link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this system")
    result = apply_plan(
        make_plan(tmp_path, candidate("build", is_dir=True)), in_git=False
    )
    assert not result.failed
    assert not build.exists()
    assert keep.exists()


def test_removal_errors_are_reported_not_hidden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write(tmp_path / "a.bin")
    monkeypatch.setattr(executor, "_remove", lambda path: (0, [(str(path), "denied")]))
    result = apply_plan(make_plan(tmp_path, candidate("a.bin")), in_git=False)
    assert not result.removed
    assert [(Path(f.path).name, f.error) for f in result.failed] == [
        ("a.bin", "denied")
    ]
