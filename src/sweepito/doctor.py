"""Environment diagnostics."""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from importlib import metadata

from sweepito import __version__, api, git, hooks
from sweepito.config import Options
from sweepito.errors import SweepitoError

MIN_PYTHON = (3, 11)


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str
    required: bool = False  # a failed required check makes doctor exit non-zero

    def to_dict(self) -> dict:
        return asdict(self)


def _dependency(name: str) -> Check:
    try:
        return Check(name, True, metadata.version(name), required=True)
    except metadata.PackageNotFoundError:
        return Check(name, False, "not installed", required=True)


def run_checks(path: str | None = None, config_file: str | None = None) -> list[Check]:
    python = sys.version_info
    checks = [
        Check("Sweepito", True, __version__),
        Check(
            "Python",
            python >= MIN_PYTHON,
            f"{python.major}.{python.minor}.{python.micro} "
            f"(requires {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+)",
            required=True,
        ),
        _dependency("pathspec"),
        _dependency("rich"),
    ]
    git_version = git.version()
    checks.append(
        Check("Git", git_version is not None, git_version or "NOT FOUND", True)
    )

    try:
        root = api.resolve_root(path)
    except SweepitoError as exc:
        checks.append(Check("Project root", False, str(exc), required=True))
        return checks
    checks.append(Check("Project root", True, str(root)))
    if git_version is None:
        return checks

    try:
        ctx = api.prepare(root, Options(), config_file)
    except SweepitoError as exc:
        checks.append(Check("Configuration", False, str(exc), required=True))
        return checks
    checks.append(
        Check(
            "Configuration",
            True,
            str(ctx.config.path) if ctx.config.path else "none (built-in defaults)",
        )
    )
    checks.append(Check("Risk ceiling", True, ctx.settings.risk.label))
    checks.append(
        Check(
            "Git repository",
            ctx.in_git,
            "yes" if ctx.in_git else "not a Git repository (cleaning is refused)",
        )
    )
    if not ctx.in_git:
        return checks

    try:
        profiles = api.scan(ctx).profiles
        checks.append(Check("Profiles", True, ", ".join(profiles)))
    except SweepitoError as exc:
        checks.append(Check("Profiles", False, str(exc)))
    for stage, installed in hooks.status(ctx.root).items():
        checks.append(
            Check(
                f"{stage} hook",
                installed,
                "installed" if installed else "not installed",
            )
        )
    return checks


def passed(checks: list[Check]) -> bool:
    return all(check.ok for check in checks if check.required)
