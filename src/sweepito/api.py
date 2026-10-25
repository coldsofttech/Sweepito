"""UI-free core API. The command line is a thin wrapper around these functions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sweepito import git
from sweepito.config import (
    FileConfig,
    Options,
    Settings,
    find_config,
    load_config,
    merge,
)
from sweepito.errors import ConfigError
from sweepito.executor import apply_plan
from sweepito.models import CleanResult, Plan
from sweepito.planner import build_plan
from sweepito.registry import Registry


@dataclass
class Context:
    root: Path
    settings: Settings
    registry: Registry
    config: FileConfig
    in_git: bool


def resolve_root(path: str | None = None) -> Path:
    """The project root: ``path``, else the git root of the cwd, else the cwd."""
    if path:
        root = Path(path).resolve()
        if not root.is_dir():
            raise ConfigError(f"Not a directory: {path}")
        return root
    cwd = Path.cwd().resolve()
    top = git.toplevel(cwd)
    return top.resolve() if top else cwd


def prepare(
    root: Path, options: Options | None = None, config_file: str | None = None
) -> Context:
    options = options or Options()
    top = git.toplevel(root)
    if config_file:
        path = Path(config_file)
        if not path.is_file():
            raise ConfigError(f"Config file not found: {config_file}")
    else:
        path = find_config(root, stop=top or root)
    config = load_config(path) if path else FileConfig()
    registry = Registry.build(config.profile_defs, config.rules)
    return Context(
        root=root,
        settings=merge(options, config),
        registry=registry,
        config=config,
        in_git=top is not None,
    )


def scan(ctx: Context) -> Plan:
    return build_plan(ctx.root, ctx.settings, ctx.registry)


def clean(ctx: Context, plan: Plan) -> CleanResult:
    return apply_plan(plan, in_git=ctx.in_git)
