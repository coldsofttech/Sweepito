"""Guards: every built-in rule and profile must have a per-profile integration case."""

from __future__ import annotations

import importlib
import pkgutil

import tests.integration as package
from tests.integration.support import REGISTRY, Case


def _all_cases() -> list[Case]:
    cases: list[Case] = []
    for module in pkgutil.iter_modules(package.__path__):
        if module.name.startswith("test_") and module.name != "test_registry_coverage":
            mod = importlib.import_module(f"{package.__name__}.{module.name}")
            cases.extend(getattr(mod, "CASES", []))  # test_custom has no profile case
    return cases


def test_every_builtin_rule_has_an_integration_case() -> None:
    covered = {rule_id for case in _all_cases() for rule_id in case.targets}
    assert covered == set(REGISTRY.rules), sorted(covered ^ set(REGISTRY.rules))


def test_every_profile_has_a_case() -> None:
    assert {case.profile for case in _all_cases()} == set(REGISTRY.profiles)


def test_case_targets_use_the_rules_own_profile() -> None:
    for case in _all_cases():
        for rule_id in case.targets:
            assert REGISTRY.rules[rule_id].profile == case.profile, rule_id


def test_one_module_per_profile() -> None:
    names = {m.name for m in pkgutil.iter_modules(package.__path__)}
    for profile in REGISTRY.profiles:
        assert f"test_{profile.replace('-', '_')}" in names, profile


def test_every_rule_with_requires_has_a_blocking_spec() -> None:
    for case in _all_cases():
        for rule_id in case.targets:
            if REGISTRY.rules[rule_id].requires:
                assert case.blocked_without.get(rule_id), rule_id
            else:
                assert rule_id not in case.blocked_without, rule_id
