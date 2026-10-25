"""Builds a cleanup plan: detect projects, match rules, apply safety gates."""

from __future__ import annotations

import os
import stat
from fnmatch import fnmatchcase
from pathlib import Path

import pathspec

from sweepito import git
from sweepito.config import Settings
from sweepito.errors import ConfigError, SafetyRefusal
from sweepito.models import Candidate, Plan, Profile, Rule, Skipped
from sweepito.registry import Registry

_GLOB_CHARS = set("*?[")


def build_plan(root: Path, settings: Settings, registry: Registry) -> Plan:
    root = root.resolve()
    in_git = git.toplevel(root) is not None
    if not in_git and not settings.no_git_check:
        raise SafetyRefusal(
            f"{root} is not inside a Git repository. Sweepito only removes "
            "git-ignored files. Pass --no-git-check to override (high impact)."
        )

    _check_rule_ids(settings, registry)
    files, entries = _inventory(root, in_git)
    marker_cache: dict[str, set[str]] = {}
    plan = Plan(root=root)
    plan.profiles = _active_profiles(settings, registry, files, marker_cache)
    rules = _select_rules(settings, registry, plan.profiles)

    # Rules that opt out of the git-ignore check must also see untracked, non-ignored
    # entries, otherwise only anchored paths could ever match them.
    untracked: list[str] = []
    if in_git and any(rule.allow_untracked for rule in rules):
        untracked = git.list_untracked(root)

    raw: dict[str, tuple[Rule, bool]] = {}
    for rule in rules:
        profile = registry.profiles[rule.profile]
        requires = rule.requires or profile.markers
        dirs = _marker_dirs(requires, files, marker_cache) if requires else {""}
        source = entries + untracked if rule.allow_untracked else entries
        for rel, is_dir in _match_rule(root, rule, dirs, source):
            raw.setdefault(rel, (rule, is_dir))

    exclude = (
        pathspec.GitIgnoreSpec.from_lines(list(settings.exclude))
        if settings.exclude
        else None
    )
    tracked_files, tracked_dirs = git.tracked(root) if in_git else (set(), set())
    survivors: list[tuple[str, Rule, bool]] = []
    for rel, (rule, is_dir) in sorted(raw.items()):
        if inside_git_dir(rel):
            plan.skipped.append(Skipped(rel, rule.id, "inside .git (never cleaned)"))
        elif exclude and _excluded(exclude, rel, is_dir):
            plan.skipped.append(Skipped(rel, rule.id, "excluded by configuration"))
        elif not confined(root, rel):
            plan.skipped.append(
                Skipped(rel, rule.id, "resolves outside the project root")
            )
        elif rel in tracked_files or rel in tracked_dirs:
            plan.skipped.append(Skipped(rel, rule.id, "tracked by git"))
        else:
            survivors.append((rel, rule, is_dir))

    if in_git:
        needs_check = [rel for rel, rule, _ in survivors if not rule.allow_untracked]
        ignored = git.check_ignored(root, needs_check)
        kept = []
        for rel, rule, is_dir in survivors:
            if rule.allow_untracked or rel in ignored:
                kept.append((rel, rule, is_dir))
            else:
                plan.skipped.append(Skipped(rel, rule.id, "not ignored by git"))
        survivors = kept

    kept_dirs: list[str] = []
    for rel, rule, is_dir in survivors:
        if any(rel.startswith(d + "/") for d in kept_dirs):
            continue  # already covered by a parent directory candidate
        if is_dir and _path_is_link(root / rel):
            is_dir = False  # a link candidate is removed as a link, never traversed
        if is_dir:
            kept_dirs.append(rel)
        size = _size(root / rel, is_dir)
        plan.candidates.append(
            Candidate(rule.id, rule.profile, rule.risk, rel, is_dir, size)
        )
    return plan


def _check_rule_ids(settings: Settings, registry: Registry) -> None:
    unknown = sorted(
        {
            rid
            for rid in (*settings.enable, *settings.disable)
            if rid not in registry.rules
        }
    )
    if unknown:
        raise ConfigError(
            f"Unknown rule ID(s): {', '.join(unknown)}. "
            "Run 'sweepito rules' to list them."
        )


def _inventory(root: Path, in_git: bool) -> tuple[list[str], list[str]]:
    """Return (non-ignored files for marker detection, entries that may be cleaned)."""
    if in_git:
        return git.list_files(root), git.list_ignored(root)
    files: list[str] = []
    entries: list[str] = []
    for current, dirnames, filenames in os.walk(root):
        rel_dir = Path(current).relative_to(root).as_posix()
        prefix = "" if rel_dir == "." else rel_dir + "/"
        if ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            files.append(prefix + name)
            entries.append(prefix + name)
        for name in dirnames:
            entries.append(prefix + name + "/")
    return files, entries


def _marker_dirs(
    requires: tuple[str, ...], files: list[str], cache: dict[str, set[str]]
) -> set[str]:
    """Directories (relative to root, '' for root) satisfying any marker."""
    found: set[str] = set()
    for marker in requires:
        if marker not in cache:
            cache[marker] = _find_marker(marker, files)
        found |= cache[marker]
    return found


def _find_marker(marker: str, files: list[str]) -> set[str]:
    segments = marker.count("/") + 1
    dirs: set[str] = set()
    for name in files:
        parts = name.split("/")
        if len(parts) < segments:
            continue
        tail = "/".join(parts[-segments:])
        if fnmatchcase(tail, marker):
            dirs.add("/".join(parts[:-segments]))
    return dirs


def _active_profiles(
    settings: Settings,
    registry: Registry,
    files: list[str],
    cache: dict[str, set[str]],
) -> list[str]:
    requested = settings.profiles
    if "auto" in requested:
        explicit = [p for p in requested if p != "auto"]
    else:
        explicit = list(requested)
    unknown = sorted(set(explicit) - set(registry.profiles))
    if unknown:
        raise ConfigError(
            f"Unknown profile(s): {', '.join(unknown)}. "
            "Run 'sweepito rules' to list them."
        )
    active: list[str] = []
    for pid, profile in registry.profiles.items():
        if "auto" in requested:
            on = (
                pid in explicit
                or profile.always
                or bool(_marker_dirs(profile.markers, files, cache))
            )
        else:
            on = pid in explicit
        if on:
            active.append(pid)
    return active


def _select_rules(
    settings: Settings, registry: Registry, active: list[str]
) -> list[Rule]:
    disabled = set(settings.disable)
    enabled = set(settings.enable)
    selected: list[Rule] = []
    for pid in active:
        profile: Profile = registry.profiles[pid]
        for rule in profile.rules:
            if rule.id in disabled:
                continue
            if rule.id in enabled or rule.risk <= settings.risk:
                selected.append(rule)
    # Enabling a rule explicitly also works outside detected profiles.
    covered = {r.id for r in selected}
    for rid in enabled - disabled - covered:
        rule = registry.rules[rid]
        if rule.profile not in active:
            selected.append(rule)
    return selected


def _split_patterns(
    patterns: tuple[str, ...],
) -> tuple[list[tuple[str, bool]], list[str]]:
    """Split into anchored literal paths (checked directly) and glob patterns."""
    literals: list[tuple[str, bool]] = []
    globs: list[str] = []
    for pattern in patterns:
        anchored = pattern.startswith("/") or "/" in pattern.rstrip("/")
        if anchored and not (_GLOB_CHARS & set(pattern)):
            literals.append((pattern.strip("/"), pattern.endswith("/")))
        else:
            globs.append(pattern)
    return literals, globs


def _match_rule(
    root: Path, rule: Rule, dirs: set[str], entries: list[str]
) -> list[tuple[str, bool]]:
    literals, globs = _split_patterns(rule.paths)
    found: list[tuple[str, bool]] = []
    for base in sorted(dirs):
        for literal, need_dir in literals:
            rel = f"{base}/{literal}" if base else literal
            try:
                st = os.lstat(root / rel)
            except OSError:
                continue
            # A link (symlink, junction) is never a directory candidate: it is only
            # ever removed as a link, so a "dir/" rule does not match it.
            is_dir = stat.S_ISDIR(st.st_mode) and not is_link(st)
            if need_dir and not is_dir:
                continue
            found.append((rel, is_dir))
    if globs:
        spec = pathspec.GitIgnoreSpec.from_lines(globs)
        for entry in entries:
            is_dir = entry.endswith("/")
            parts = entry.rstrip("/").split("/")
            for i in range(len(parts)):
                if "/".join(parts[:i]) not in dirs:
                    continue
                rel = "/".join(parts[i:]) + ("/" if is_dir else "")
                if spec.match_file(rel):
                    found.append(("/".join(parts), is_dir))
                    break
    return found


def _excluded(spec: pathspec.GitIgnoreSpec, rel: str, is_dir: bool) -> bool:
    parts = rel.split("/")
    for i in range(len(parts)):
        last = i == len(parts) - 1
        prefix = "/".join(parts[: i + 1]) + ("/" if (not last or is_dir) else "")
        if spec.match_file(prefix):
            return True
    return False


def inside_git_dir(rel: str) -> bool:
    """True for ``.git`` itself or anything below it, in this repo or a nested one."""
    return ".git" in rel.split("/")


_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def is_link(st: os.stat_result) -> bool:
    """True for a symlink or, on Windows, any reparse point such as a junction.

    CPython 3.11 reports a junction as an ordinary directory, so ``S_ISLNK`` alone
    would let a recursive walk follow it out of the project. ``st`` must come from
    ``lstat`` or ``DirEntry.stat(follow_symlinks=False)``.
    """
    if stat.S_ISLNK(st.st_mode):
        return True
    return bool(getattr(st, "st_file_attributes", 0) & _REPARSE_POINT)


def _path_is_link(path: Path) -> bool:
    try:
        return is_link(os.lstat(path))
    except OSError:
        return False


def confined(root: Path, rel: str) -> bool:
    """True if the parent of ``rel`` resolves inside the root (links not followed)."""
    if ".." in rel.split("/"):
        return False
    parent = os.path.realpath((root / rel).parent)
    root_real = os.path.realpath(root)
    try:
        return os.path.commonpath([parent, root_real]) == root_real
    except ValueError:
        return False


def _size(path: Path, is_dir: bool) -> int:
    try:
        st = os.lstat(path)
        if not is_dir or is_link(st):
            return st.st_size  # a link counts as the link, never its target
    except OSError:
        return 0
    total = 0
    stack = [str(path)]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        entry_stat = entry.stat(follow_symlinks=False)
                        if is_link(entry_stat):
                            total += entry_stat.st_size
                        elif stat.S_ISDIR(entry_stat.st_mode):
                            stack.append(entry.path)
                        else:
                            total += entry_stat.st_size
                    except OSError:
                        continue
        except OSError:
            continue
    return total
