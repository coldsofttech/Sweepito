"""Human-readable output (CLI only). Every command renders through Rich."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sweepito.doctor import Check
from sweepito.models import CleanResult, Plan, Profile, Rule, format_size

LABEL_STYLE = "bold cyan"
RISK_STYLE = {
    "custom": "blue",
    "safe": "green",
    "configurable": "yellow",
    "high-impact": "bold red",
}


def make_console(no_color: bool = False, stderr: bool = False) -> Console:
    return Console(highlight=False, no_color=no_color, stderr=stderr, soft_wrap=True)


def _risk(label: str) -> Text:
    return Text(label, style=RISK_STYLE.get(label, ""))


def _info_panel(title: str, rows: list[tuple[str, str]]) -> Panel:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style=LABEL_STYLE)
    grid.add_column(overflow="fold")
    for label, value in rows:
        grid.add_row(label, Text(value))
    return Panel(grid, title=title, border_style="cyan")


def success(console: Console, message: str) -> None:
    console.print(Text(message, style="green"))


def info(console: Console, message: str) -> None:
    console.print(Text(message))


def warning(console: Console, message: str) -> None:
    console.print(Text(message, style="yellow"))


def error(console: Console, message: str) -> None:
    console.print(Text(f"sweepito: error: {message}", style="bold red"))


def print_plan(console: Console, plan: Plan, verbose: bool = False) -> None:
    console.print(
        Text.assemble(
            ("Project: ", LABEL_STYLE),
            str(plan.root),
            ("   profiles: ", LABEL_STYLE),
            ", ".join(plan.profiles),
        )
    )
    if plan.candidates:
        table = Table(title="Cleanup candidates")
        table.add_column("Rule", style="cyan")
        table.add_column("Path", overflow="fold")
        table.add_column("Size", justify="right")
        table.add_column("Risk")
        for cand in plan.candidates:
            table.add_row(
                cand.rule,
                Text(cand.path + ("/" if cand.is_dir else "")),
                format_size(cand.size),
                _risk(cand.risk.label),
            )
        console.print(table)
    if verbose or not plan.candidates:
        for skipped in plan.skipped:
            warning(
                console, f"skipped {skipped.path} ({skipped.rule}): {skipped.reason}"
            )


def print_summary(console: Console, plan: Plan, *, deleting: bool = False) -> None:
    count = len(plan.candidates)
    skipped = f" Skipped {len(plan.skipped)} protected path(s)." if plan.skipped else ""
    if not count:
        info(console, "Nothing to clean." + skipped)
        return
    console.print(
        Text.assemble(
            (f"{count} candidate(s), ", "bold"),
            (f"{format_size(plan.total_bytes)} reclaimable.", "bold green"),
            skipped,
        )
    )
    if not deleting:
        info(console, "Nothing deleted. Run 'sweepito clean' to remove them.")


def print_result(console: Console, result: CleanResult) -> None:
    if result.removed:
        success(
            console,
            f"Removed {len(result.removed)} item(s), "
            f"{format_size(result.freed_bytes)} freed.",
        )
    for failure in result.failed:
        console.print(Text(f"failed: {failure.path}: {failure.error}", style="red"))
    for skipped in result.skipped:
        warning(console, f"skipped: {skipped.path}: {skipped.reason}")


def print_report(
    console: Console, root: str, groups: dict[str, dict[str, dict]], total: int
) -> None:
    console.print(Text.assemble(("Project: ", LABEL_STYLE), root))
    for kind, entries in groups.items():
        table = Table(title=f"By {kind}", title_justify="left")
        table.add_column(kind.capitalize(), style="cyan" if kind != "risk" else "")
        table.add_column("Items", justify="right")
        if kind == "rule":
            table.add_column("Risk")
        table.add_column("Size", justify="right")
        for key, slot in sorted(entries.items(), key=lambda kv: -kv[1]["bytes"]):
            name = _risk(key) if kind == "risk" else Text(key)
            cells = [name, str(slot["count"])]
            if kind == "rule":
                cells.append(_risk(slot["risk"]))
            cells.append(format_size(slot["bytes"]))
            table.add_row(*cells)
        console.print(table)
    console.print(
        Text.assemble(
            "Total reclaimable if everything were enabled: ",
            (format_size(total), "bold green"),
        )
    )


def print_rules(console: Console, rules: list[Rule]) -> None:
    table = Table(title="Sweepito rules")
    table.add_column("Profile", style="cyan")
    table.add_column("Rule")
    table.add_column("Risk")
    table.add_column("Default")
    table.add_column("Description", overflow="fold")
    previous = None
    for rule in rules:
        if previous is not None and rule.profile != previous:
            table.add_section()
        table.add_row(
            rule.profile if rule.profile != previous else "",
            rule.id,
            _risk(rule.risk.label),
            Text("on", style="green")
            if rule.risk.label in ("safe", "custom")
            else "opt-in",
            rule.description,
        )
        previous = rule.profile
    console.print(table)


def _markers(profile: Profile) -> str:
    return ", ".join(profile.markers) if profile.markers else "always active"


def print_profiles(console: Console, profiles: list[Profile]) -> None:
    table = Table(title="Sweepito profiles")
    table.add_column("Profile", style="cyan", no_wrap=True)
    table.add_column("Description", overflow="fold", min_width=11)
    table.add_column("Detected by", overflow="fold")
    table.add_column("Rules", justify="right", no_wrap=True)
    table.add_column("Safe", justify="right", style="green", no_wrap=True)
    table.add_column("Configurable", justify="right", style="yellow", no_wrap=True)
    table.add_column("High-impact", justify="right", style="red", no_wrap=True)
    show_custom = any(p.risk_counts()["custom"] for p in profiles)
    if show_custom:
        table.add_column("Custom", justify="right", style="blue", no_wrap=True)
    for profile in profiles:
        counts = profile.risk_counts()
        cells = [
            profile.id,
            profile.description,
            _markers(profile),
            str(len(profile.rules)),
            str(counts["safe"]),
            str(counts["configurable"]),
            str(counts["high-impact"]),
        ]
        if show_custom:
            cells.append(str(counts["custom"]))
        table.add_row(*cells)
    console.print(table)


def print_profile_detail(console: Console, profile: Profile) -> None:
    counts = profile.risk_counts()
    breakdown = ", ".join(f"{n} {label}" for label, n in counts.items() if n) or "none"
    rows = [
        ("Description", profile.description or "-"),
        ("Detected by", _markers(profile)),
        ("Rules", f"{len(profile.rules)} ({breakdown})"),
    ]
    console.print(_info_panel(f"Profile {profile.id}", rows))
    if profile.rules:
        print_rules(console, list(profile.rules))


def print_rule_detail(console: Console, details: dict) -> None:
    rows = [
        ("Profile", details["profile"]),
        ("Risk", details["risk"]),
        ("Paths", ", ".join(details["paths"])),
        ("Requires", ", ".join(details["requires"]) or "-"),
        ("Allow untracked", "yes" if details["allow_untracked"] else "no"),
        ("Description", details["description"] or "-"),
    ]
    console.print(_info_panel(f"Rule {details['id']}", rows))


def print_config(console: Console, payload: dict) -> None:
    settings = payload["settings"]

    def listing(values: list[str]) -> str:
        return ", ".join(values) or "-"

    rows = [
        ("Config file", payload["config_file"] or "none (built-in defaults)"),
        ("Profiles", listing(settings["profiles"])),
        ("Risk ceiling", settings["risk"]),
        ("Enabled rules", listing(settings["enable"])),
        ("Disabled rules", listing(settings["disable"])),
        ("Excluded paths", listing(settings["exclude"])),
        ("Custom rules", listing(payload["custom_rules"])),
    ]
    console.print(_info_panel("Sweepito configuration", rows))


def print_hook_status(console: Console, state: dict[str, bool]) -> None:
    table = Table(title="Sweepito hooks")
    table.add_column("Stage")
    table.add_column("State")
    for stage, installed in state.items():
        state_text = (
            Text("installed", style="green")
            if installed
            else Text("not installed", style="yellow")
        )
        table.add_row(stage, state_text)
    console.print(table)


def print_checks(console: Console, checks: list[Check]) -> None:
    table = Table(title="Sweepito doctor")
    table.add_column("Check")
    table.add_column("Result")
    table.add_column("Details", overflow="fold")
    for check in checks:
        if check.ok:
            result = Text("OK", style="green")
        else:
            result = Text("FAILED" if check.required else "MISSING", style="red")
        table.add_row(check.name, result, Text(check.detail))
    console.print(table)
