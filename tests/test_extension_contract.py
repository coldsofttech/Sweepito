"""Pins the JSON the VS Code extension (extensions/vscode) reads from the CLI.

If one of these fails, the extension's parser and types in
extensions/vscode/src/cli/types.ts need the same change.
"""

from __future__ import annotations

import re

import pytest

from sweepito.cli import main
from tests.conftest import Repo

CANDIDATE_KEYS = {"rule", "profile", "risk", "path", "is_dir", "size"}


@pytest.fixture
def project(repo: Repo) -> Repo:
    repo.write("pyproject.toml", "[project]\nname = 'x'\n")
    repo.write(".gitignore", "__pycache__/\n")
    repo.write("src/__pycache__/a.pyc", "x")
    return repo


def test_scan_document_shape(project: Repo) -> None:
    code, doc = project.json("scan")
    assert code == 0
    assert {
        "root",
        "profiles",
        "candidates",
        "skipped",
        "total_bytes",
        "dry_run",
    } <= set(doc)
    assert set(doc["candidates"][0]) == CANDIDATE_KEYS


def test_clean_dry_run_matches_scan(project: Repo) -> None:
    _, scan = project.json("scan")
    code, dry = project.json("clean", "--dry-run")
    assert code == 0
    assert dry["candidates"] == scan["candidates"]


def test_clean_document_shape(project: Repo) -> None:
    code, doc = project.json("clean", "--yes")
    assert code == 0
    assert {"removed", "failed", "freed_bytes"} <= set(doc)
    assert set(doc["removed"][0]) == CANDIDATE_KEYS


def test_rules_document_shape(project: Repo) -> None:
    _, doc = project.json("rules")
    assert {"id", "profile", "risk", "default", "description"} <= set(doc["rules"][0])


def test_doctor_document_shape(project: Repo) -> None:
    _, doc = project.json("doctor")
    assert isinstance(doc["healthy"], bool)
    assert {"name", "ok", "detail", "required"} <= set(doc["checks"][0])


def test_hook_status_is_a_stage_to_bool_map(project: Repo) -> None:
    _, doc = project.json("hook", "status")
    assert set(doc) == {"post-commit", "pre-commit"}
    assert all(isinstance(v, bool) for v in doc.values())


def test_version_banner_is_parseable(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--version"])
    assert re.fullmatch(r"sweepito \d+\.\d+\.\d+\S*", capsys.readouterr().out.strip())
