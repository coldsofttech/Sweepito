"""Keeps the generated profile documentation honest."""

from __future__ import annotations

import importlib.util
import re
import shlex
from pathlib import Path

import pytest

from sweepito.cli import build_parser
from sweepito.config import load_config
from sweepito.registry import Registry
from tests.conftest import Repo

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "generate_profiles_doc.py"
REGISTRY = Registry.build()


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_profiles_doc", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATOR = load_generator()
DOCS = GENERATOR.PROFILE_DOCS


def test_every_profile_is_documented_and_nothing_extra() -> None:
    assert set(DOCS) == set(REGISTRY.profiles)


@pytest.mark.parametrize("profile", sorted(DOCS))
def test_config_snippet_loads_and_references_real_rules(
    profile: str, tmp_path: Path
) -> None:
    path = tmp_path / "sweepito.toml"
    path.write_text(DOCS[profile]["toml"], encoding="utf-8")
    cfg = load_config(path)
    registry = Registry.build(cfg.profile_defs, cfg.rules)
    for rule_id in (*cfg.enable, *cfg.disable):
        assert rule_id in registry.rules, f"{profile}: unknown rule {rule_id}"


@pytest.mark.parametrize("profile", sorted(DOCS))
def test_cli_example_parses_and_references_real_rules(profile: str) -> None:
    args = shlex.split(DOCS[profile]["cli"])
    assert args[0] == "sweepito"
    parsed = build_parser().parse_args(args[1:])
    for rule_id in (*parsed.enable, *parsed.disable):
        assert rule_id in REGISTRY.rules, f"{profile}: unknown rule {rule_id}"
    for name in parsed.profiles:
        assert name in REGISTRY.profiles


@pytest.mark.parametrize("profile", sorted(DOCS))
def test_snippet_works_end_to_end(profile: str, repo: Repo) -> None:
    repo.write("sweepito.toml", DOCS[profile]["toml"])
    code, _, err = repo.run("scan", str(repo.root))
    assert code == 0, err


FILE_EXTENSIONS = {
    "lock", "gradle", "xml", "json", "toml", "yaml", "yml", "hcl", "swift", "rb",
    "exs", "mod", "work", "ninja", "tf", "dump", "kts", "iml", "ipynb", "txt",
}  # fmt: skip


def test_notes_mention_only_real_rule_ids() -> None:
    token = re.compile(r"`([a-z][a-z0-9-]*)\.([a-z][a-z0-9-]*)`")
    prefixes = {rule_id.split(".")[0] for rule_id in REGISTRY.rules}
    for profile, docs in DOCS.items():
        for note in docs["notes"]:
            for prefix, name in token.findall(note):
                if name in FILE_EXTENSIONS or prefix not in prefixes:
                    continue  # a file name such as symfony.lock, not a rule ID
                assert f"{prefix}.{name}" in REGISTRY.rules, (
                    f"{profile}: note mentions unknown rule {prefix}.{name}"
                )


def test_committed_profiles_doc_is_up_to_date() -> None:
    committed = (ROOT / "docs" / "profiles.md").read_text(encoding="utf-8")
    assert committed == GENERATOR.render(), (
        "docs/profiles.md is stale; run: uv run python scripts/generate_profiles_doc.py"
    )
