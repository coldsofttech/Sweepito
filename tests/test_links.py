"""Links (symlinks and Windows junctions) must never be followed out of a candidate."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from sweepito.planner import is_link
from tests.conftest import Repo

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="Windows junctions")


def make_junction(link: Path, target: Path) -> None:
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        check=True,
        capture_output=True,
    )


def make_symlink(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this system")


def project_with_sibling(repo: Repo) -> Path:
    """An ignored build/ directory, plus a sibling directory that must survive."""
    repo.write("pyproject.toml", "[project]\nname='x'\n")
    repo.write(".gitignore", "build/\n")
    repo.write("build/real.o", "object")
    repo.write("other/keep.txt", "tracked source")
    repo.write("other/scratch.txt", "uncommitted work")
    repo.write("other/big.bin", "x" * 5000)
    repo.git("add", "other/keep.txt")
    return repo.root / "other"


def assert_sibling_untouched(repo: Repo) -> None:
    assert repo.exists("other/keep.txt")
    assert repo.exists("other/scratch.txt")
    assert (repo.root / "other" / "big.bin").read_text() == "x" * 5000


# ---- the shared link check -------------------------------------------------------


def test_is_link_recognises_symlinks_and_reparse_points() -> None:
    plain_dir = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x10)
    symlink = SimpleNamespace(st_mode=stat.S_IFLNK)
    # CPython 3.11 reports a junction as a plain directory with the reparse bit set.
    junction = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x10 | 0x400)
    posix_dir = SimpleNamespace(st_mode=stat.S_IFDIR)
    assert is_link(symlink)
    assert is_link(junction)
    assert not is_link(plain_dir)
    assert not is_link(posix_dir)


# ---- a link nested inside an ignored candidate directory -------------------------


@windows_only
def test_junction_inside_a_candidate_is_removed_not_followed(repo: Repo) -> None:
    other = project_with_sibling(repo)
    make_junction(repo.root / "build" / "link", other)
    code, data = repo.json("clean", "--yes", "--risk", "configurable")
    assert code == 0 and data["failed"] == []
    assert not repo.exists("build")
    assert_sibling_untouched(repo)


@windows_only
def test_junction_target_is_not_counted_in_the_reclaimable_size(repo: Repo) -> None:
    other = project_with_sibling(repo)
    make_junction(repo.root / "build" / "link", other)
    code, data = repo.json("scan", "--risk", "configurable")
    [candidate] = data["candidates"]
    assert candidate["path"] == "build"
    assert candidate["size"] < 1000  # not the 5000+ bytes behind the junction


def test_symlink_inside_a_candidate_is_removed_not_followed(repo: Repo) -> None:
    other = project_with_sibling(repo)
    make_symlink(repo.root / "build" / "link", other)
    code, data = repo.json("clean", "--yes", "--risk", "configurable")
    assert code == 0 and data["failed"] == []
    assert not repo.exists("build")
    assert_sibling_untouched(repo)


# ---- the candidate itself is a link ----------------------------------------------


@windows_only
def test_a_junction_named_like_a_directory_rule_is_not_a_candidate(repo: Repo) -> None:
    other = project_with_sibling(repo)
    (repo.root / "build" / "real.o").unlink()
    (repo.root / "build").rmdir()
    make_junction(repo.root / "build", other)
    assert repo.candidates("--risk", "configurable") == {}
    repo.json("clean", "--yes", "--risk", "configurable")
    assert_sibling_untouched(repo)


@windows_only
def test_a_junction_matched_as_a_file_path_is_removed_as_a_link(repo: Repo) -> None:
    other = project_with_sibling(repo)
    (repo.root / "build" / "real.o").unlink()
    (repo.root / "build").rmdir()
    make_junction(repo.root / "build", other)
    repo.write(
        "sweepito.toml", '[[rule]]\nid = "custom.build-link"\npaths = ["/build"]\n'
    )
    code, data = repo.json("clean", "--yes", "--risk", "custom")
    assert code == 0 and data["failed"] == []
    assert not repo.exists("build")
    assert_sibling_untouched(repo)


def test_a_symlink_matched_as_a_file_path_is_removed_as_a_link(repo: Repo) -> None:
    other = project_with_sibling(repo)
    (repo.root / "build" / "real.o").unlink()
    (repo.root / "build").rmdir()
    make_symlink(repo.root / "build", other)
    repo.write(
        "sweepito.toml", '[[rule]]\nid = "custom.build-link"\npaths = ["/build"]\n'
    )
    code, data = repo.json("clean", "--yes", "--risk", "custom")
    assert code == 0 and data["failed"] == []
    assert not repo.exists("build")
    assert_sibling_untouched(repo)
