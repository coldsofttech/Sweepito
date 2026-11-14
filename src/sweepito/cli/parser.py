"""The argparse definition of every command and option."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

RISK_CHOICES = ["custom", "safe", "configurable", "high-impact"]


def _global_parent() -> argparse.ArgumentParser:
    import argparse

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
    import argparse

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
    import argparse

    from sweepito import __version__, hooks
    from sweepito.cli.commands import (
        cmd_check,
        cmd_clean,
        cmd_config,
        cmd_doctor,
        cmd_hook,
        cmd_init,
        cmd_profiles,
        cmd_report,
        cmd_rules,
        cmd_scan,
    )

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
