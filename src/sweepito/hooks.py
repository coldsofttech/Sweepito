"""Install, remove and inspect the native Git hook."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from sweepito import git
from sweepito.errors import ConfigError

BEGIN = "# >>> sweepito >>>"
END = "# <<< sweepito <<<"
STAGES = {
    "post-commit": "sweepito clean --hook --non-interactive --quiet",
    "pre-commit": "sweepito scan --hook --quiet",
}


def _block(stage: str) -> str:
    command = STAGES[stage]
    return (
        f"{BEGIN}\n"
        f"if command -v sweepito >/dev/null 2>&1; then\n"
        f'  {command} || echo "sweepito: {stage} hook failed" >&2\n'
        f"fi\n"
        f"{END}\n"
    )


def hook_path(root: Path, stage: str) -> Path:
    if stage not in STAGES:
        raise ConfigError(
            f"Unsupported hook stage {stage!r}; use post-commit or pre-commit."
        )
    return git.hooks_dir(root) / stage


def _strip(text: str) -> str:
    if BEGIN not in text:
        return text
    head, _, rest = text.partition(BEGIN)
    _, _, tail = rest.partition(END)
    return (head.rstrip("\n") + "\n" + tail.lstrip("\n")).strip("\n")


def install(root: Path, stage: str = "post-commit") -> Path:
    path = hook_path(root, stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    base = _strip(existing)
    if not base:
        base = "#!/bin/sh"
    path.write_text(
        base.rstrip("\n") + "\n\n" + _block(stage), encoding="utf-8", newline="\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def uninstall(root: Path, stage: str = "post-commit") -> bool:
    """Remove the Sweepito block. Returns True if one was removed."""
    path = hook_path(root, stage)
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if BEGIN not in text:
        return False
    remaining = _strip(text)
    if remaining.strip() in ("", "#!/bin/sh"):
        os.unlink(path)
    else:
        path.write_text(remaining + "\n", encoding="utf-8", newline="\n")
    return True


def status(root: Path) -> dict[str, bool]:
    result = {}
    for stage in STAGES:
        path = hook_path(root, stage)
        result[stage] = path.exists() and BEGIN in path.read_text(encoding="utf-8")
    return result
