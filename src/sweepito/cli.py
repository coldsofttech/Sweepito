"""Command line interface: a thin wrapper over :mod:`sweepito.api`."""

from __future__ import annotations

import argparse
import json
import sys

from sweepito import __version__, api, doctor, git, hooks
from sweepito.config import Options
from sweepito.errors import (
    EXIT_FAILED,
    EXIT_INTERRUPTED,
    EXIT_OK,
    EXIT_UNEXPECTED,
    EXIT_USAGE,
    ConfigError,
    SafetyRefusal,
    SweepitoError,
)
from sweepito.models import Plan, Risk, format_size
from sweepito.planner import build_plan
from sweepito.registry import Registry
from sweepito.ui import (
    error,
    info,
    make_console,
    print_checks,
    print_config,
    print_hook_status,
    print_plan,
    print_profile_detail,
    print_profiles,
    print_report,
    print_result,
    print_rule_detail,
    print_rules,
    print_summary,
    success,
    warning,
)

RISK_CHOICES = ["custom", "safe", "configurable", "high-impact"]


def _global_parent() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument(
        "--config", metavar="FILE", help="Use this config file (skips discovery)."
    )
    p.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    p.add_argument("-q", "--quiet", action="store_true", help="Print only when needed.")
    p.add_argument(
        "-v", "--verbose", action="store_true", help="Explain skipped paths."
    )
    p.add_argument("--no-color", action="store_true", help="Disable colored output.")
    p.add_argument("--hook", action="store_true", help=argparse.SUPPRESS)
    return p


def _selection_parent() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("path", nargs="?", help="Project root (default: git root or cwd).")
    p.add_argument(
        "-p",
        "--profile",
        action="append",
        default=[],
        dest="profiles",
        metavar="NAME",
        help="Only use this profile (repeatable).",
    )
    p.add_argument(
        "--enable",
        action="append",
        default=[],
        metavar="RULE",
        help="Enable a rule by ID (repeatable).",
    )
    p.add_argument(
        "--disable",
        action="append",
        default=[],
        metavar="RULE",
        help="Disable a rule by ID (repeatable).",
    )
    p.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Never touch matching paths (repeatable).",
    )
    p.add_argument(
        "--risk",
        choices=RISK_CHOICES,
        help="Highest risk level to include (custom: only your own rules).",
    )
    p.add_argument(
        "--no-git-check",
        action="store_true",
        help="Allow running outside a Git repository (high impact).",
    )
    return p


def build_parser() -> argparse.ArgumentParser:
    glob, sel = _global_parent(), _selection_parent()
    parser = argparse.ArgumentParser(
        prog="sweepito",
        description="Safely clean caches and build artifacts across technologies.",
    )
    parser.add_argument(
        "--version", action="version", version=f"sweepito {__version__}"
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    scan = sub.add_parser("scan", parents=[glob, sel], help="List cleanup candidates.")
    scan.set_defaults(func=cmd_scan)

    clean = sub.add_parser(
        "clean", parents=[glob, sel], help="Delete cleanup candidates."
    )
    clean.add_argument("-n", "--dry-run", action="store_true", help="Same as scan.")
    clean.add_argument(
        "-y", "--yes", action="store_true", help="Do not ask for confirmation."
    )
    clean.add_argument(
        "--non-interactive",
        action="store_true",
        help="Never prompt; proceed with the configured rules.",
    )
    clean.set_defaults(func=cmd_clean)

    check = sub.add_parser(
        "check", parents=[glob, sel], help="Exit with code 1 if candidates exist."
    )
    check.set_defaults(func=cmd_check)

    report = sub.add_parser(
        "report",
        parents=[glob, sel],
        help="Summarise reclaimable space by profile, rule and risk.",
    )
    report.set_defaults(func=cmd_report)

    rules = sub.add_parser("rules", parents=[glob], help="List profiles and rules.")
    rules.add_argument("path", nargs="?", help="Project root (for custom rules).")
    rules.add_argument("-p", "--profile", action="append", default=[], dest="profiles")
    rules.add_argument(
        "--risk", choices=RISK_CHOICES, help="Only rules at exactly this risk level."
    )
    rules.add_argument("--explain", metavar="RULE", help="Describe one rule.")
    rules.set_defaults(func=cmd_rules)

    profiles = sub.add_parser("profiles", parents=[glob], help="List profiles.")
    profiles.add_argument("path", nargs="?", help="Project root (for custom profiles).")
    profiles.add_argument("--explain", metavar="PROFILE", help="Describe one profile.")
    profiles.set_defaults(func=cmd_profiles)

    cfg = sub.add_parser("config", help="Show or validate configuration.")
    cfg_sub = cfg.add_subparsers(dest="action", metavar="ACTION", required=True)
    for name, text in (
        ("show", "Show effective settings."),
        ("validate", "Validate the configuration."),
    ):
        leaf = cfg_sub.add_parser(name, parents=[glob], help=text)
        leaf.add_argument("path", nargs="?", help="Project root.")
        leaf.set_defaults(func=cmd_config)

    init = sub.add_parser("init", parents=[glob], help="Write a starter sweepito.toml.")
    init.add_argument("path", nargs="?", help="Project root.")
    init.add_argument(
        "--force", action="store_true", help="Overwrite an existing file."
    )
    init.set_defaults(func=cmd_init)

    hook = sub.add_parser("hook", help="Manage the native Git hook.")
    hook_sub = hook.add_subparsers(dest="action", metavar="ACTION", required=True)
    for name, text in (
        ("install", "Install the hook."),
        ("uninstall", "Remove the hook."),
        ("status", "Show installed hooks."),
    ):
        leaf = hook_sub.add_parser(name, parents=[glob], help=text)
        leaf.add_argument("path", nargs="?", help="Project root.")
        if name != "status":
            leaf.add_argument(
                "--stage", choices=sorted(hooks.STAGES), default="post-commit"
            )
        leaf.set_defaults(func=cmd_hook)

    doc = sub.add_parser("doctor", parents=[glob], help="Diagnose the environment.")
    doc.add_argument("path", nargs="?", help="Project root.")
    doc.set_defaults(func=cmd_doctor)
    return parser


def _options(args: argparse.Namespace) -> Options:
    return Options(
        profiles=tuple(getattr(args, "profiles", ()) or ()),
        enable=tuple(getattr(args, "enable", ()) or ()),
        disable=tuple(getattr(args, "disable", ()) or ()),
        exclude=tuple(getattr(args, "exclude", ()) or ()),
        risk=(Risk.parse(args.risk) if getattr(args, "risk", None) else None),
        no_git_check=getattr(args, "no_git_check", False),
        hook=args.hook,
    )


def _context(args: argparse.Namespace) -> api.Context:
    root = api.resolve_root(args.path)
    return api.prepare(root, _options(args), args.config)


def _emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def _plan(args: argparse.Namespace) -> tuple[api.Context, Plan]:
    ctx = _context(args)
    return ctx, api.scan(ctx)


def _quiet(args: argparse.Namespace, ctx: api.Context) -> bool:
    return args.quiet or ctx.settings.quiet


def _scan_and_report(args: argparse.Namespace) -> Plan:
    ctx, plan = _plan(args)
    if args.json:
        _emit({**plan.to_dict(), "dry_run": True})
        return plan
    console = make_console(args.no_color)
    if _quiet(args, ctx):
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


def _confirm(count: int, size: int) -> bool:
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


def cmd_clean(args: argparse.Namespace) -> int:
    ctx, plan = _plan(args)
    quiet = _quiet(args, ctx)
    console = make_console(args.no_color)
    if args.dry_run:
        if args.json:
            _emit({**plan.to_dict(), "dry_run": True})
        else:
            print_plan(console, plan, args.verbose)
            print_summary(console, plan)
        return EXIT_OK
    if not plan.candidates:
        if args.json:
            _emit({**plan.to_dict(), "dry_run": False, **_empty_result()})
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
        if not _confirm(len(plan.candidates), plan.total_bytes):
            info(console, "Aborted. Nothing deleted.")
            return EXIT_OK
    result = api.clean(ctx, plan)
    if args.json:
        _emit({**plan.to_dict(), "dry_run": False, **result.to_dict()})
    elif not quiet or result.failed:
        print_result(make_console(args.no_color, stderr=quiet), result)
    return EXIT_FAILED if result.failed else EXIT_OK


def _empty_result() -> dict:
    return {"removed": [], "failed": [], "freed_bytes": 0}


def cmd_report(args: argparse.Namespace) -> int:
    ctx = _context(args)
    # Informational only: plan everything, delete nothing.
    from dataclasses import replace

    settings = replace(ctx.settings, risk=Risk.HIGH_IMPACT)
    plan = build_plan(ctx.root, settings, ctx.registry)
    groups: dict[str, dict[str, dict]] = {"profile": {}, "rule": {}, "risk": {}}
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
        _emit({"root": str(plan.root), "total_bytes": plan.total_bytes, **groups})
        return EXIT_OK
    print_report(make_console(args.no_color), str(plan.root), groups, plan.total_bytes)
    return EXIT_OK


def cmd_rules(args: argparse.Namespace) -> int:
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
            "requires": list(rule.requires or registry.profiles[rule.profile].markers),
            "description": rule.description,
            "allow_untracked": rule.allow_untracked,
        }
        if args.json:
            _emit(details)
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
        _emit(
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
    root = api.resolve_root(args.path)
    registry = api.prepare(root, Options(hook=args.hook), args.config).registry
    if args.explain:
        profile = registry.profiles.get(args.explain)
        if profile is None:
            raise ConfigError(f"Unknown profile {args.explain!r}.")
        if args.json:
            _emit(
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
                            "requires": list(r.requires or profile.markers),
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
        _emit(
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
    ctx = _context(args)
    if args.action == "validate":
        if args.json:
            _emit({"valid": True})
        else:
            success(make_console(args.no_color), "Configuration OK.")
        return EXIT_OK
    payload = {
        "config_file": str(ctx.config.path) if ctx.config.path else None,
        "settings": ctx.settings.to_dict(),
        "custom_rules": [r.id for r in ctx.config.rules],
    }
    if args.json:
        _emit(payload)
    else:
        print_config(make_console(args.no_color), payload)
    return EXIT_OK


_TEMPLATE = """\
# Sweepito configuration. See 'sweepito rules' for rule IDs.

[defaults]
profiles = ["auto"]   # or an explicit list, e.g. ["python", "node"]
risk = "safe"         # custom | safe | configurable | high-impact

[clean]
enable = []           # e.g. ["rust.target", "node.next"]
disable = []
exclude = []          # e.g. ["dist/", "build/keep-me/"]

[hook]
quiet = true

# Custom path rule: only git-ignored, untracked paths are ever removed.
# [[rule]]
# id = "custom.test-output"
# paths = ["test-results/", "tmp/e2e/**"]
"""


def cmd_init(args: argparse.Namespace) -> int:
    root = api.resolve_root(args.path)
    target = root / "sweepito.toml"
    if target.exists() and not args.force:
        raise SafetyRefusal(f"{target} already exists. Use --force to overwrite.")
    ctx = api.prepare(root, Options(), args.config)
    detected = api.scan(ctx).profiles if ctx.in_git else []
    header = (
        f"# Detected profiles: {', '.join(detected) or 'none'}\n" if detected else ""
    )
    target.write_text(header + _TEMPLATE, encoding="utf-8", newline="\n")
    success(make_console(args.no_color), f"Wrote {target}")
    return EXIT_OK


def cmd_hook(args: argparse.Namespace) -> int:
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
            _emit(state)
        else:
            print_hook_status(console, state)
    return EXIT_OK


def cmd_doctor(args: argparse.Namespace) -> int:
    checks = doctor.run_checks(args.path, args.config)
    healthy = doctor.passed(checks)
    if args.json:
        _emit({"healthy": healthy, "checks": [c.to_dict() for c in checks]})
    else:
        print_checks(make_console(args.no_color), checks)
    return EXIT_OK if healthy else EXIT_FAILED


def _stderr(args: argparse.Namespace):
    return make_console(getattr(args, "no_color", False), stderr=True)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return EXIT_USAGE
    try:
        return args.func(args)
    except SweepitoError as exc:
        error(_stderr(args), str(exc))
        return exc.exit_code
    except KeyboardInterrupt:
        warning(_stderr(args), "sweepito: interrupted")
        return EXIT_INTERRUPTED
    except Exception as exc:  # noqa: BLE001 - last-resort handler
        error(_stderr(args), f"unexpected error: {exc!r}")
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    raise SystemExit(main())
