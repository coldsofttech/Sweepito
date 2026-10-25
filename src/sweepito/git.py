"""Thin wrappers around the git command line.

All paths passed in and returned are posix-style and relative to ``root``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from sweepito.errors import GitError


def _run(
    root: Path,
    args: list[str],
    *,
    data: bytes | None = None,
    ok: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[bytes]:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            input=data,
            capture_output=True,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        raise GitError("The git executable was not found on PATH.") from exc
    if proc.returncode not in ok:
        detail = proc.stderr.decode(errors="replace").strip()
        raise GitError(f"git {args[0]} failed: {detail}")
    return proc


def _split(output: bytes) -> list[str]:
    return [
        p.decode("utf-8", errors="surrogateescape") for p in output.split(b"\0") if p
    ]


def version() -> str | None:
    try:
        proc = subprocess.run(["git", "--version"], capture_output=True, check=False)
    except FileNotFoundError:
        return None
    return proc.stdout.decode(errors="replace").strip() or None


def toplevel(path: Path) -> Path | None:
    """Return the work tree root containing ``path``, or None if not in a repo."""
    if not path.is_dir():
        return None
    proc = _run(path, ["rev-parse", "--show-toplevel"], ok=(0, 128))
    if proc.returncode != 0:
        return None
    return Path(proc.stdout.decode(errors="replace").strip())


def hooks_dir(root: Path) -> Path:
    proc = _run(root, ["rev-parse", "--git-path", "hooks"])
    path = Path(proc.stdout.decode(errors="replace").strip())
    return path if path.is_absolute() else (root / path).resolve()


def list_files(root: Path) -> list[str]:
    """Tracked files plus untracked files that are not ignored."""
    proc = _run(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    return _split(proc.stdout)


def list_ignored(root: Path) -> list[str]:
    """Ignored, untracked entries. Fully ignored directories end with a slash."""
    proc = _run(
        root,
        [
            "ls-files",
            "-z",
            "--others",
            "--ignored",
            "--exclude-standard",
            "--directory",
        ],
    )
    return _split(proc.stdout)


def list_untracked(root: Path) -> list[str]:
    """Untracked, non-ignored files plus every directory above them (trailing slash).

    Files are listed individually, not collapsed, so patterns can match inside an
    untracked directory.
    """
    proc = _run(root, ["ls-files", "-z", "--others", "--exclude-standard"])
    files = _split(proc.stdout)
    dirs: set[str] = set()
    for name in files:
        parent = name.rpartition("/")[0]
        while parent and parent not in dirs:
            dirs.add(parent)
            parent = parent.rpartition("/")[0]
    return files + sorted(d + "/" for d in dirs)


def tracked(root: Path) -> tuple[set[str], set[str]]:
    """Return (tracked files, every directory that contains a tracked file)."""
    proc = _run(root, ["ls-files", "-z", "--cached"])
    files = set(_split(proc.stdout))
    dirs: set[str] = set()
    for name in files:
        parent = name.rpartition("/")[0]
        while parent and parent not in dirs:
            dirs.add(parent)
            parent = parent.rpartition("/")[0]
    return files, dirs


def check_ignored(root: Path, paths: list[str]) -> set[str]:
    """Return the subset of ``paths`` that git ignores."""
    if not paths:
        return set()
    data = b"".join(p.encode("utf-8", errors="surrogateescape") + b"\0" for p in paths)
    proc = _run(root, ["check-ignore", "-z", "--stdin"], data=data, ok=(0, 1))
    return set(_split(proc.stdout))
