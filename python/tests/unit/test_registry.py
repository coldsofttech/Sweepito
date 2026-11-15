from __future__ import annotations

import pytest

from sweepito.errors import ConfigError
from sweepito.models import Risk, Rule
from sweepito.registry import CUSTOM_PROFILE, Registry


def custom_rule(rule_id: str, profile: str = CUSTOM_PROFILE) -> Rule:
    return Rule(
        id=rule_id,
        profile=profile,
        paths=("out/",),
        risk=Risk.CUSTOM,
        builtin=False,
    )


def test_builtin_registry_is_consistent() -> None:
    registry = Registry.build()
    assert registry.profiles
    assert registry.rules
    for profile in registry.profiles.values():
        for rule in profile.rules:
            assert rule.profile == profile.id
            assert registry.rules[rule.id] is rule


def test_builtin_rules_are_marked_builtin() -> None:
    assert all(rule.builtin for rule in Registry.build().rules.values())


def test_custom_profile_is_added_with_its_markers() -> None:
    registry = Registry.build({"myteam": (("team.toml",), "Team stuff")})
    profile = registry.profiles["myteam"]
    assert profile.markers == ("team.toml",)
    assert profile.description == "Team stuff"
    assert profile.rules == ()


def test_custom_profile_extends_a_builtin_one() -> None:
    builtin = Registry.build().profiles["python"]
    registry = Registry.build({"python": (("extra.cfg",), "")})
    merged = registry.profiles["python"]
    assert merged.markers == builtin.markers + ("extra.cfg",)
    assert merged.description == builtin.description
    assert merged.rules == builtin.rules


def test_custom_profile_description_overrides_the_builtin_one() -> None:
    registry = Registry.build({"python": ((), "Mine")})
    assert registry.profiles["python"].description == "Mine"


def test_custom_rule_without_a_profile_creates_one() -> None:
    rule = custom_rule("custom.out")
    registry = Registry.build(custom_rules=(rule,))
    assert registry.rules["custom.out"] is rule
    assert registry.profiles[CUSTOM_PROFILE].description == "User-defined rules"
    assert registry.profiles[CUSTOM_PROFILE].always


def test_custom_rule_joins_an_existing_profile() -> None:
    rule = custom_rule("python.mine", profile="python")
    registry = Registry.build(custom_rules=(rule,))
    assert rule in registry.profiles["python"].rules
    assert len(registry.profiles["python"].rules) > 1


def test_duplicate_rule_ids_are_rejected() -> None:
    existing = next(iter(Registry.build().rules))
    with pytest.raises(ConfigError, match="Duplicate rule ID"):
        Registry.build(custom_rules=(custom_rule(existing),))
