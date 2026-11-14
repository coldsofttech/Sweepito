from __future__ import annotations

import io
from pathlib import Path

import pytest
from rich.console import Console

from sweepito import ui
from sweepito.doctor import Check
from sweepito.models import (
    Candidate,
    CleanResult,
    Failure,
    Plan,
    Profile,
    Risk,
    Rule,
    Skipped,
)


class Capture:
    """A Rich console writing to memory, wide enough that nothing wraps."""

    def __init__(self) -> None:
        self.buffer = io.StringIO()
        self.console = Console(
            file=self.buffer, width=200, highlight=False, no_color=True
        )

    @property
    def text(self) -> str:
        return self.buffer.getvalue()


@pytest.fixture
def out() -> Capture:
    return Capture()


def sample_plan() -> Plan:
    plan = Plan(root=Path("proj"), profiles=["python", "node"])
    plan.candidates.append(
        Candidate("python.cache", "python", Risk.SAFE, "a", False, 10)
    )
    plan.candidates.append(
        Candidate("node.modules", "node", Risk.HIGH_IMPACT, "d", True, 2048)
    )
    plan.skipped.append(Skipped("src/x", "python.cache", "tracked by git"))
    return plan


def rule(rule_id: str, risk: Risk) -> Rule:
    return Rule(id=rule_id, profile="python", paths=("x/",), risk=risk, description="d")


def test_make_console_honours_stderr_and_color_flags() -> None:
    console = ui.make_console(no_color=True, stderr=True)
    assert console.stderr is True
    assert console.no_color is True


def test_message_helpers(out: Capture) -> None:
    ui.success(out.console, "done")
    ui.info(out.console, "plain")
    ui.warning(out.console, "careful")
    ui.error(out.console, "bad")
    assert out.text.splitlines() == ["done", "plain", "careful", "sweepito: error: bad"]


def test_print_plan_lists_candidates_with_size_and_risk(out: Capture) -> None:
    ui.print_plan(out.console, sample_plan())
    text = out.text
    assert "Project: proj" in text and "python, node" in text
    assert "python.cache" in text and "node.modules" in text
    assert "d/" in text  # directories get a trailing slash
    assert "2.0 KB" in text and "high-impact" in text
    assert "skipped" not in text  # hidden unless verbose


def test_print_plan_shows_skipped_when_verbose_or_nothing_found(out: Capture) -> None:
    ui.print_plan(out.console, sample_plan(), verbose=True)
    assert "skipped src/x (python.cache): tracked by git" in out.text
    empty = Capture()
    plan = Plan(root=Path("proj"))
    plan.skipped.append(Skipped("src/x", "r", "tracked by git"))
    ui.print_plan(empty.console, plan)
    assert "skipped src/x (r): tracked by git" in empty.text
    assert "Cleanup candidates" not in empty.text


def test_print_summary_with_candidates(out: Capture) -> None:
    ui.print_summary(out.console, sample_plan())
    assert "2 candidate(s), 2.0 KB reclaimable." in out.text
    assert "Skipped 1 protected path(s)." in out.text
    assert "Nothing deleted" in out.text


def test_print_summary_while_deleting_omits_the_dry_run_note(out: Capture) -> None:
    ui.print_summary(out.console, sample_plan(), deleting=True)
    assert "Nothing deleted" not in out.text


def test_print_summary_with_nothing_to_clean(out: Capture) -> None:
    ui.print_summary(out.console, Plan(root=Path("proj")))
    assert out.text.strip() == "Nothing to clean."


def test_print_result_reports_removed_failed_and_skipped(out: Capture) -> None:
    result = CleanResult(freed_bytes=1024)
    result.removed.append(Candidate("r", "p", Risk.SAFE, "a", False, 1024))
    result.failed.append(Failure("b", "denied"))
    result.skipped.append(Skipped("c", "r", "tracked by git"))
    ui.print_result(out.console, result)
    assert "Removed 1 item(s), 1.0 KB freed." in out.text
    assert "failed: b: denied" in out.text
    assert "skipped: c: tracked by git" in out.text


def test_print_report_has_a_table_per_grouping_and_a_total(out: Capture) -> None:
    groups = {
        "profile": {"python": {"count": 2, "bytes": 2048}},
        "rule": {"python.cache": {"count": 2, "bytes": 2048, "risk": "safe"}},
        "risk": {"safe": {"count": 2, "bytes": 2048}},
    }
    ui.print_report(out.console, "proj", groups, 2048)
    text = out.text
    assert "By profile" in text and "By rule" in text and "By risk" in text
    assert "python.cache" in text
    assert "Total reclaimable if everything were enabled: 2.0 KB" in text


def test_print_rules_marks_defaults_and_opt_in(out: Capture) -> None:
    ui.print_rules(
        out.console,
        [rule("python.cache", Risk.SAFE), rule("python.venv", Risk.HIGH_IMPACT)],
    )
    lines = {line for line in out.text.splitlines() if "python." in line}
    assert any("python.cache" in line and " on " in line for line in lines)
    assert any("python.venv" in line and "opt-in" in line for line in lines)


def test_print_profiles_and_detail(out: Capture) -> None:
    always = Profile("common", "Everywhere", (), (rule("c.tmp", Risk.SAFE),))
    marked = Profile("python", "Python", ("pyproject.toml",), ())
    ui.print_profiles(out.console, [always, marked])
    assert "common" in out.text and "always active" in out.text
    assert "pyproject.toml" in out.text
    assert "Custom" not in out.text
    detail = Capture()
    ui.print_profile_detail(detail.console, always)
    assert "Profile common" in detail.text and "1 (1 safe)" in detail.text
    assert "c.tmp" in detail.text


def test_print_profiles_adds_a_custom_column_when_needed(out: Capture) -> None:
    profile = Profile("mine", "", (), (rule("custom.out", Risk.CUSTOM),))
    ui.print_profiles(out.console, [profile])
    assert "Custom" in out.text


def test_print_rule_detail_and_config(out: Capture) -> None:
    ui.print_rule_detail(
        out.console,
        {
            "id": "python.cache",
            "profile": "python",
            "risk": "safe",
            "paths": ["__pycache__/", "*.pyc"],
            "requires": [],
            "description": "",
            "allow_untracked": False,
        },
    )
    assert "Rule python.cache" in out.text
    assert "__pycache__/, *.pyc" in out.text
    config = Capture()
    ui.print_config(
        config.console,
        {
            "config_file": None,
            "settings": {
                "profiles": ["auto"],
                "risk": "safe",
                "enable": [],
                "disable": [],
                "exclude": [],
            },
            "custom_rules": [],
        },
    )
    assert "none (built-in defaults)" in config.text
    assert "Sweepito configuration" in config.text


def test_print_hook_status(out: Capture) -> None:
    ui.print_hook_status(out.console, {"post-commit": True, "pre-commit": False})
    assert "installed" in out.text and "not installed" in out.text


def test_print_checks_distinguishes_failed_and_missing(out: Capture) -> None:
    ui.print_checks(
        out.console,
        [
            Check("Python", True, "3.11"),
            Check("Git", False, "NOT FOUND", required=True),
            Check("Hook", False, "not installed"),
        ],
    )
    lines = out.text.splitlines()
    assert any("Python" in line and "OK" in line for line in lines)
    assert any("Git" in line and "FAILED" in line for line in lines)
    assert any("Hook" in line and "MISSING" in line for line in lines)
