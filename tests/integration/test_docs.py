"""Keeps the hand-written profile documentation in step with the built-in profiles."""

from __future__ import annotations

import re
from pathlib import Path

from sweepito.registry import Registry

ROOT = Path(__file__).resolve().parents[2]
PROFILES_DIR = ROOT / "docs" / "profiles"
INDEX = ROOT / "docs" / "profiles.md"
REGISTRY = Registry.build()


def test_every_profile_has_its_own_page() -> None:
    missing = [p for p in REGISTRY.profiles if not (PROFILES_DIR / f"{p}.md").is_file()]
    assert not missing, f"docs/profiles/ has no page for: {sorted(missing)}"


def test_no_page_documents_an_unknown_profile() -> None:
    pages = {path.stem for path in PROFILES_DIR.glob("*.md")}
    extra = pages - set(REGISTRY.profiles)
    assert not extra, f"docs/profiles/ documents unknown profiles: {sorted(extra)}"


def test_index_links_to_every_profile_page() -> None:
    linked = set(
        re.findall(r"\[`([a-z0-9-]+)`\]\(profiles/\1\.md\)", INDEX.read_text("utf-8"))
    )
    assert linked == set(REGISTRY.profiles)


def test_each_page_names_its_rules() -> None:
    for profile in REGISTRY.profiles.values():
        text = (PROFILES_DIR / f"{profile.id}.md").read_text(encoding="utf-8")
        for rule in profile.rules:
            assert f"`{rule.id}`" in text, f"{profile.id}.md does not mention {rule.id}"
