"""Deletes planned candidates. Failures are reported, never worked around."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from sweepito import git
from sweepito.models import CleanResult, Failure, Plan, Skipped
from sweepito.planner import confined, inside_git_dir, is_link


def apply_plan(plan: Plan, *, in_git: bool = True) -> CleanResult:
    result = CleanResult()
    root = plan.root
    # Re-read tracked state right before deleting, in case it changed since planning.
    tracked_files, tracked_dirs = git.tracked(root) if in_git else (set(), set())
    for cand in plan.candidates:
        if cand.path in tracked_files or cand.path in tracked_dirs:
            result.skipped.append(Skipped(cand.path, cand.rule, "tracked by git"))
            continue
        if inside_git_dir(cand.path):
            result.skipped.append(
                Skipped(cand.path, cand.rule, "inside .git (never cleaned)")
            )
            continue
        if not confined(root, cand.path):
            result.skipped.append(
                Skipped(cand.path, cand.rule, "resolves outside the project root")
            )
            continue
        freed, errors = _remove(root / cand.path)
        result.freed_bytes += freed
        if errors:
            result.failed.extend(Failure(p, msg) for p, msg in errors)
        else:
            result.removed.append(cand)
    return result


def _remove(path: Path) -> tuple[int, list[tuple[str, str]]]:
    """Remove a file, link or directory tree.

    Links (symlinks, and on Windows junctions and other reparse points) are removed
    as links and never traversed, so nothing outside the tree can be deleted through
    them.
    """
    freed = 0
    errors: list[tuple[str, str]] = []
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return 0, []
    except OSError as exc:
        return 0, [(str(path), str(exc))]

    if is_link(st) or not stat.S_ISDIR(st.st_mode):
        return _unlink(path)

    stack = [str(path)]
    order: list[str] = []
    while stack:
        current = stack.pop()
        order.append(current)
        try:
            with os.scandir(current) as it:
                children = list(it)
        except OSError as exc:
            errors.append((current, str(exc)))
            continue
        for child in children:
            try:
                child_stat = child.stat(follow_symlinks=False)
            except OSError as exc:
                errors.append((child.path, str(exc)))
                continue
            if stat.S_ISDIR(child_stat.st_mode) and not is_link(child_stat):
                stack.append(child.path)
            else:
                size, errs = _unlink(Path(child.path))
                freed += size
                errors.extend(errs)
    for directory in reversed(order):
        try:
            os.rmdir(directory)
        except OSError as exc:
            errors.append((directory, str(exc)))
    return freed, errors


def _unlink(path: Path) -> tuple[int, list[tuple[str, str]]]:
    """Remove one file or link; a directory link goes without touching its target."""
    try:
        st = os.lstat(path)
        directory_link = stat.S_ISDIR(st.st_mode) or bool(
            getattr(st, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_DIRECTORY", 0x10)
        )
        if directory_link:
            os.rmdir(path)  # removes a junction or directory symlink, not its contents
        else:
            os.unlink(path)
    except FileNotFoundError:
        return 0, []
    except OSError as exc:
        return 0, [(str(path), str(exc))]
    return st.st_size, []
