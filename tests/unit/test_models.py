from __future__ import annotations

from pathlib import Path

import pytest

from sweepito.errors import ConfigError
from sweepito.models import (
    Candidate,
    CleanResult,
    Failure,
    Plan,
    Profile,
    Risk,
    Rule,
    Skipped,
    format_size,
)


def rule(rule_id: str, risk: Risk) -> Rule:
    return Rule(id=rule_id, profile="p", paths=("x/",), risk=risk)


@pytest.mark.parametrize(
    ("risk", "label"),
    [
        (Risk.CUSTOM, "custom"),
        (Risk.SAFE, "safe"),
        (Risk.CONFIGURABLE, "configurable"),
        (Risk.HIGH_IMPACT, "high-impact"),
    ],
)
def test_risk_label_round_trips_through_parse(risk: Risk, label: str) -> None:
    assert risk.label == label
    assert Risk.parse(label) is risk


def test_risk_parse_is_forgiving_about_case_and_spacing() -> None:
    assert Risk.parse("  High-Impact ") is Risk.HIGH_IMPACT


@pytest.mark.parametrize("value", ["nope", "", 3, None])
def test_risk_parse_rejects_unknown_values(value: object) -> None:
    with pytest.raises(ConfigError, match="Invalid risk level"):
        Risk.parse(value)


def test_risk_levels_are_ordered_with_custom_lowest() -> None:
    assert Risk.CUSTOM < Risk.SAFE < Risk.CONFIGURABLE < Risk.HIGH_IMPACT


def test_profile_without_markers_is_always_active() -> None:
    assert Profile("p", "", (), ()).always
    assert not Profile("p", "", ("setup.py",), ()).always


def test_profile_risk_counts() -> None:
    profile = Profile(
        "p",
        "",
        (),
        (rule("a", Risk.SAFE), rule("b", Risk.SAFE), rule("c", Risk.HIGH_IMPACT)),
    )
    assert profile.risk_counts() == {
        "safe": 2,
        "configurable": 0,
        "high-impact": 1,
        "custom": 0,
    }


def test_candidate_skipped_and_failure_to_dict() -> None:
    cand = Candidate("r", "p", Risk.SAFE, "build", True, 12)
    assert cand.to_dict() == {
        "rule": "r",
        "profile": "p",
        "risk": "safe",
        "path": "build",
        "is_dir": True,
        "size": 12,
    }
    assert Skipped("a", "r", "why").to_dict() == {
        "path": "a",
        "rule": "r",
        "reason": "why",
    }
    assert Failure("a", "boom").to_dict() == {"path": "a", "error": "boom"}


def test_plan_totals_and_to_dict() -> None:
    plan = Plan(root=Path("proj"))
    assert plan.total_bytes == 0
    plan.profiles.append("python")
    plan.candidates.append(Candidate("r", "python", Risk.SAFE, "a", False, 10))
    plan.candidates.append(Candidate("r", "python", Risk.SAFE, "b", True, 5))
    plan.skipped.append(Skipped("c", "r", "tracked by git"))
    data = plan.to_dict()
    assert data["root"] == "proj"
    assert data["profiles"] == ["python"]
    assert data["total_bytes"] == 15
    assert [c["path"] for c in data["candidates"]] == ["a", "b"]
    assert data["skipped"] == [{"path": "c", "rule": "r", "reason": "tracked by git"}]


def test_clean_result_to_dict() -> None:
    result = CleanResult()
    result.removed.append(Candidate("r", "p", Risk.SAFE, "a", False, 3))
    result.failed.append(Failure("b", "denied"))
    result.skipped.append(Skipped("c", "r", "why"))
    result.freed_bytes = 3
    data = result.to_dict()
    assert data["freed_bytes"] == 3
    assert data["removed"][0]["path"] == "a"
    assert data["failed"] == [{"path": "b", "error": "denied"}]
    assert data["skipped"][0]["path"] == "c"


@pytest.mark.parametrize(
    ("size", "text"),
    [
        (0, "0 B"),
        (1023, "1023 B"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1024**2, "1.0 MB"),
        (1024**3, "1.0 GB"),
        (1024**4, "1.0 TB"),
        (1024**5, "1024.0 TB"),
    ],
)
def test_format_size(size: int, text: str) -> None:
    assert format_size(size) == text
