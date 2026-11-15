"""Small helpers shared by the command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import argparse

    from rich.console import Console

    from sweepito import api
    from sweepito.config import Options
    from sweepito.models import Plan


def build_options(args: argparse.Namespace) -> Options:
    from sweepito.config import Options
    from sweepito.models import Risk

    return Options(
        profiles=tuple(getattr(args, "profiles", ()) or ()),
        enable=tuple(getattr(args, "enable", ()) or ()),
        disable=tuple(getattr(args, "disable", ()) or ()),
        exclude=tuple(getattr(args, "exclude", ()) or ()),
        risk=(Risk.parse(args.risk) if getattr(args, "risk", None) else None),
        no_git_check=getattr(args, "no_git_check", False),
        hook=args.hook,
    )


def get_context(args: argparse.Namespace) -> api.Context:
    from sweepito import api

    root = api.resolve_root(args.path)
    return api.prepare(root, build_options(args), args.config)


def emit(payload: dict[str, Any]) -> None:
    import json

    print(json.dumps(payload, indent=2))


def get_plan(args: argparse.Namespace) -> tuple[api.Context, Plan]:
    from sweepito import api

    ctx = get_context(args)
    return ctx, api.scan(ctx)


def is_quiet(args: argparse.Namespace, ctx: api.Context) -> bool:
    return args.quiet or ctx.settings.quiet


def confirm(count: int, size: int) -> bool:
    import sys

    from sweepito.errors import SafetyRefusal
    from sweepito.models import format_size

    if not sys.stdin.isatty():
        return False
    try:
        answer = input(f"Delete {count} item(s), {format_size(size)}? [y/N] ")
    except EOFError:
        raise SafetyRefusal(
            "Confirmation required but no input is available. "
            "Pass --yes or --non-interactive."
        ) from None
    return answer.strip().lower() in ("y", "yes")


def empty_result() -> dict[str, Any]:
    return {"removed": [], "failed": [], "freed_bytes": 0}


def stderr_console(args: argparse.Namespace) -> Console:
    from sweepito.ui import make_console

    return make_console(getattr(args, "no_color", False), stderr=True)
