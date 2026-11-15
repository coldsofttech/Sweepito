from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sweepito import git
from sweepito.errors import GitError


def init_repo(root: Path) -> Path:
    root.mkdir(exist_ok=True)
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    return root


def write(root: Path, rel: str, content: str = "x") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def stage(root: Path, *rels: str) -> None:
    subprocess.run(["git", "-C", str(root), "add", *rels], check=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = init_repo(tmp_path / "proj")
    write(root, ".gitignore", "build/\n*.log\n")
    write(root, "src/app.py")
    write(root, "src/pkg/mod.py")
    write(root, "notes.txt")
    write(root, "build/out.o")
    write(root, "debug.log")
    stage(root, ".gitignore", "src")
    return root


def test_version_reports_git_or_none_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (git.version() or "").startswith("git version")

    def missing(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", missing)
    assert git.version() is None


def test_missing_git_executable_is_a_git_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", missing)
    with pytest.raises(GitError, match="not found"):
        git.toplevel(tmp_path)


def test_toplevel_is_none_for_a_missing_directory_or_non_repo(tmp_path: Path) -> None:
    assert git.toplevel(tmp_path / "missing") is None
    assert git.toplevel(tmp_path) is None


def test_toplevel_finds_the_repository_root(repo: Path) -> None:
    top = git.toplevel(repo / "src" / "pkg")
    assert top is not None
    assert top.resolve() == repo.resolve()


def test_failing_git_command_raises_with_the_command_name(tmp_path: Path) -> None:
    with pytest.raises(GitError, match="ls-files failed"):
        git.list_files(tmp_path)


def test_list_files_has_tracked_and_unignored_untracked(repo: Path) -> None:
    files = set(git.list_files(repo))
    assert {"src/app.py", "src/pkg/mod.py", "notes.txt", ".gitignore"} <= files
    assert "build/out.o" not in files
    assert "debug.log" not in files


def test_list_ignored_collapses_ignored_directories(repo: Path) -> None:
    ignored = set(git.list_ignored(repo))
    assert "build/" in ignored
    assert "debug.log" in ignored
    assert "src/app.py" not in ignored


def test_list_untracked_lists_files_and_their_parent_directories(repo: Path) -> None:
    write(repo, "scratch/deep/a.txt")
    untracked = git.list_untracked(repo)
    assert "notes.txt" in untracked
    assert "scratch/deep/a.txt" in untracked
    assert "scratch/" in untracked and "scratch/deep/" in untracked
    assert "build/out.o" not in untracked


def test_tracked_returns_files_and_every_parent_directory(repo: Path) -> None:
    files, dirs = git.tracked(repo)
    assert files == {".gitignore", "src/app.py", "src/pkg/mod.py"}
    assert dirs == {"src", "src/pkg"}


def test_check_ignored_returns_only_the_ignored_subset(repo: Path) -> None:
    ignored = git.check_ignored(repo, ["build/out.o", "notes.txt", "debug.log"])
    assert ignored == {"build/out.o", "debug.log"}


def test_check_ignored_with_no_paths_does_not_call_git(
    tmp_path: Path,
) -> None:
    assert git.check_ignored(tmp_path, []) == set()


def test_hooks_dir_is_an_absolute_path_ending_in_hooks(repo: Path) -> None:
    directory = git.hooks_dir(repo)
    assert directory.is_absolute()
    assert directory.name == "hooks"
