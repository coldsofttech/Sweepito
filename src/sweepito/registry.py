"""Loads built-in technology profiles and merges user-defined ones."""

from __future__ import annotations

import tomllib
from dataclasses import replace
from importlib import resources

from sweepito.errors import ConfigError
from sweepito.models import Profile, Risk, Rule

CUSTOM_PROFILE = "custom"


def _load_builtin() -> dict[str, Profile]:
    profiles: dict[str, Profile] = {}
    package = resources.files("sweepito.profiles")
    for entry in sorted(package.iterdir(), key=lambda e: e.name):
        if not entry.name.endswith(".toml"):
            continue
        data = tomllib.loads(entry.read_text(encoding="utf-8"))
        pid = data["id"]
        rules = tuple(
            Rule(
                id=raw["id"],
                profile=pid,
                paths=tuple(raw["paths"]),
                risk=Risk.parse(raw["risk"]),
                requires=tuple(raw.get("requires", ())),
                description=raw.get("description", ""),
            )
            for raw in data.get("rule", [])
        )
        profiles[pid] = Profile(
            id=pid,
            description=data.get("description", ""),
            markers=tuple(data.get("markers", ())),
            rules=rules,
        )
    return profiles


class Registry:
    """All known profiles and rules, built-in plus custom."""

    def __init__(self, profiles: dict[str, Profile]) -> None:
        self.profiles = profiles
        self.rules: dict[str, Rule] = {}
        for profile in profiles.values():
            for rule in profile.rules:
                if rule.id in self.rules:
                    raise ConfigError(f"Duplicate rule ID {rule.id!r}.")
                self.rules[rule.id] = rule

    @classmethod
    def build(
        cls,
        custom_profiles: dict[str, tuple[tuple[str, ...], str]] | None = None,
        custom_rules: tuple[Rule, ...] = (),
    ) -> Registry:
        profiles = _load_builtin()
        for name, (markers, description) in (custom_profiles or {}).items():
            existing = profiles.get(name)
            if existing:
                profiles[name] = replace(
                    existing,
                    markers=existing.markers + markers,
                    description=description or existing.description,
                )
            else:
                profiles[name] = Profile(name, description, markers, ())
        for rule in custom_rules:
            profile = profiles.get(rule.profile)
            if profile is None:
                profile = Profile(rule.profile, "User-defined rules", (), ())
            profiles[rule.profile] = replace(profile, rules=profile.rules + (rule,))
        return cls(profiles)
