"""Command handlers: parse the namespace, call the API, render the result."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sweepito.cli.helpers import (
    confirm,
    emit,
    empty_result,
    get_context,
    get_plan,
    is_quiet,
)
from sweepito.errors import EXIT_FAILED, EXIT_OK

if TYPE_CHECKING:
    import argparse
    from typing import Any

    from sweepito.models import Plan
    from sweepito.registry import Registry


def _scan_and_report(args: argparse.Namespace) -> Plan:
    from sweepito.models import format_size
    from sweepito.ui import info, make_console, print_plan, print_summary

    ctx, plan = get_plan(args)
    if args.json:
        emit({**plan.to_dict(), "dry_run": True})
        return plan
    console = make_console(args.no_color)
    if is_quiet(args, ctx):
        if plan.candidates:
            info(
                console,
                f"sweepito: {len(plan.candidates)} cleanup candidate(s), "
                f"{format_size(plan.total_bytes)} reclaimable (run 'sweepito scan').",
            )
        return plan
    print_plan(console, plan, args.verbose)
    print_summary(console, plan)
    return plan


def cmd_scan(args: argparse.Namespace) -> int:
    _scan_and_report(args)
    return EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    plan = _scan_and_report(args)
    return EXIT_FAILED if plan.candidates else EXIT_OK


def cmd_clean(args: argparse.Namespace) -> int:
    import sys

    from sweepito import api
    from sweepito.errors import SafetyRefusal
    from sweepito.ui import (
        info,
        make_console,
        print_plan,
        print_result,
        print_summary,
    )

    ctx, plan = get_plan(args)
    quiet = is_quiet(args, ctx)
    console = make_console(args.no_color)
    if args.dry_run:
        if args.json:
            emit({**plan.to_dict(), "dry_run": True})
        else:
            print_plan(console, plan, args.verbose)
            print_summary(console, plan)
        return EXIT_OK
    if not plan.candidates:
        if args.json:
            emit({**plan.to_dict(), "dry_run": False, **empty_result()})
        elif not quiet:
            print_summary(console, plan, deleting=True)
        return EXIT_OK
    if not (args.yes or args.non_interactive):
        if not sys.stdin.isatty():
            raise SafetyRefusal(
                "Confirmation required but no terminal is attached. "
                "Pass --yes or --non-interactive."
            )
        print_plan(console, plan, args.verbose)
        if not confirm(len(plan.candidates), plan.total_bytes):
            info(console, "Aborted. Nothing deleted.")
            return EXIT_OK
    result = api.clean(ctx, plan)
    if args.json:
        emit({**plan.to_dict(), "dry_run": False, **result.to_dict()})
    elif not quiet or result.failed:
        print_result(make_console(args.no_color, stderr=quiet), result)
    return EXIT_FAILED if result.failed else EXIT_OK


def cmd_report(args: argparse.Namespace) -> int:
    from dataclasses import replace

    from sweepito.models import Risk
    from sweepito.planner import build_plan
    from sweepito.ui import make_console, print_report

    ctx = get_context(args)
    # Informational only: plan everything, delete nothing.
    settings = replace(ctx.settings, risk=Risk.HIGH_IMPACT)
    plan = build_plan(ctx.root, settings, ctx.registry)
    groups: dict[str, dict[str, dict[str, Any]]] = {
        "profile": {},
        "rule": {},
        "risk": {},
    }
    for cand in plan.candidates:
        for kind, key in (
            ("profile", cand.profile),
            ("rule", cand.rule),
            ("risk", cand.risk.label),
        ):
            slot = groups[kind].setdefault(key, {"count": 0, "bytes": 0})
            if kind == "rule":
                slot["risk"] = cand.risk.label
            slot["count"] += 1
            slot["bytes"] += cand.size
    if args.json:
        emit({"root": str(plan.root), "total_bytes": plan.total_bytes, **groups})
        return EXIT_OK
    print_report(make_console(args.no_color), str(plan.root), groups, plan.total_bytes)
    return EXIT_OK


def cmd_rules(args: argparse.Namespace) -> int:
    from sweepito import api
    from sweepito.config import Options
    from sweepito.errors import ConfigError
    from sweepito.models import Risk
    from sweepito.ui import make_console, print_rule_detail, print_rules

    root = api.resolve_root(args.path)
    ctx = api.prepare(root, Options(hook=args.hook), args.config)
    registry: Registry = ctx.registry
    if args.explain:
        rule = registry.rules.get(args.explain)
        if rule is None:
            raise ConfigError(f"Unknown rule ID {args.explain!r}.")
        details = {
            "id": rule.id,
            "profile": rule.profile,
            "risk": rule.risk.label,
            "paths": list(rule.paths),
            "requires": list(rule.any_markers(registry.profiles[rule.profile].markers)),
            "requires_all": list(rule.requires_all),
            "description": rule.description,
            "allow_untracked": rule.allow_untracked,
        }
        if args.json:
            emit(details)
        else:
            print_rule_detail(make_console(args.no_color), details)
        return EXIT_OK
    rows = []
    for profile in registry.profiles.values():
        if args.profiles and profile.id not in args.profiles:
            continue
        for rule in profile.rules:
            if args.risk and rule.risk.label != args.risk:
                continue
            rows.append(rule)
    if args.json:
        emit(
            {
                "rules": [
                    {
                        "id": r.id,
                        "profile": r.profile,
                        "risk": r.risk.label,
                        "default": r.risk in (Risk.SAFE, Risk.CUSTOM),
                        "description": r.description,
                    }
                    for r in rows
                ]
            }
        )
        return EXIT_OK
    print_rules(make_console(args.no_color), rows)
    return EXIT_OK


def cmd_profiles(args: argparse.Namespace) -> int:
    from sweepito import api
    from sweepito.config import Options
    from sweepito.errors import ConfigError
    from sweepito.ui import make_console, print_profile_detail, print_profiles

    root = api.resolve_root(args.path)
    registry = api.prepare(root, Options(hook=args.hook), args.config).registry
    if args.explain:
        profile = registry.profiles.get(args.explain)
        if profile is None:
            raise ConfigError(f"Unknown profile {args.explain!r}.")
        if args.json:
            emit(
                {
                    "id": profile.id,
                    "description": profile.description,
                    "markers": list(profile.markers),
                    "always_active": profile.always,
                    "rules": [
                        {
                            "id": r.id,
                            "risk": r.risk.label,
                            "paths": list(r.paths),
                            "requires": list(r.any_markers(profile.markers)),
                            "requires_all": list(r.requires_all),
                            "description": r.description,
                        }
                        for r in profile.rules
                    ],
                }
            )
        else:
            print_profile_detail(make_console(args.no_color), profile)
        return EXIT_OK
    profiles = list(registry.profiles.values())
    if args.json:
        emit(
            {
                "profiles": [
                    {
                        "id": p.id,
                        "description": p.description,
                        "markers": list(p.markers),
                        "always_active": p.always,
                        "rules": len(p.rules),
                        **{k.replace("-", "_"): v for k, v in p.risk_counts().items()},
                    }
                    for p in profiles
                ]
            }
        )
    else:
        print_profiles(make_console(args.no_color), profiles)
    return EXIT_OK


def cmd_config(args: argparse.Namespace) -> int:
    from sweepito.ui import make_console, print_config, success

    ctx = get_context(args)
    if args.action == "validate":
        if args.json:
            emit({"valid": True})
        else:
            success(make_console(args.no_color), "Configuration OK.")
        return EXIT_OK
    payload = {
        "config_file": str(ctx.config.path) if ctx.config.path else None,
        "settings": ctx.settings.to_dict(),
        "custom_rules": [r.id for r in ctx.config.rules],
    }
    if args.json:
        emit(payload)
    else:
        print_config(make_console(args.no_color), payload)
    return EXIT_OK


def cmd_init(args: argparse.Namespace) -> int:
    from importlib import resources

    from sweepito import api
    from sweepito.config import Options
    from sweepito.errors import SafetyRefusal
    from sweepito.ui import make_console, success

    root = api.resolve_root(args.path)
    target = root / "sweepito.toml"
    if target.exists() and not args.force:
        raise SafetyRefusal(f"{target} already exists. Use --force to overwrite.")
    ctx = api.prepare(root, Options(), args.config)
    detected = api.scan(ctx).profiles if ctx.in_git else []
    header = (
        f"# Detected profiles: {', '.join(detected) or 'none'}\n" if detected else ""
    )
    template = (
        resources.files("sweepito.cli") / "templates" / "sweepito.toml.tmpl"
    ).read_text(encoding="utf-8")
    target.write_text(header + template, encoding="utf-8", newline="\n")
    success(make_console(args.no_color), f"Wrote {target}")
    return EXIT_OK


def cmd_hook(args: argparse.Namespace) -> int:
    from sweepito import api, git, hooks
    from sweepito.errors import SafetyRefusal
    from sweepito.ui import info, make_console, print_hook_status, success

    root = api.resolve_root(args.path)
    if git.toplevel(root) is None:
        raise SafetyRefusal("Hooks need a Git repository.")
    console = make_console(args.no_color)
    if args.action == "install":
        path = hooks.install(root, args.stage)
        success(console, f"Installed {args.stage} hook: {path}")
    elif args.action == "uninstall":
        if hooks.uninstall(root, args.stage):
            success(console, f"Removed {args.stage} hook.")
        else:
            info(console, f"No {args.stage} hook installed.")
    else:
        state = hooks.status(root)
        if args.json:
            emit(state)
        else:
            print_hook_status(console, state)
    return EXIT_OK


def cmd_doctor(args: argparse.Namespace) -> int:
    from sweepito import doctor
    from sweepito.ui import make_console, print_checks

    checks = doctor.run_checks(args.path, args.config)
    healthy = doctor.passed(checks)
    if args.json:
        emit({"healthy": healthy, "checks": [c.to_dict() for c in checks]})
    else:
        print_checks(make_console(args.no_color), checks)
    return EXIT_OK if healthy else EXIT_FAILED
