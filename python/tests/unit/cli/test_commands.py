from __future__ import annotations

import json
from pathlib import Path

import pytest

from sweepito.cli import main
from sweepito.errors import EXIT_FAILED, EXIT_OK, EXIT_REFUSED, EXIT_USAGE

CUSTOM_RULE = '[[rule]]\nid = "custom.out"\npaths = ["out/"]\n'


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A non-git project with one custom rule matching out/."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / "sweepito.toml").write_text(CUSTOM_RULE, encoding="utf-8")
    (root / "out").mkdir()
    (root / "out" / "artifact.bin").write_text("x" * 100, encoding="utf-8")
    (root / "keep.txt").write_text("source", encoding="utf-8")
    return root


class Runner:
    def __init__(self, capsys: pytest.CaptureFixture[str]) -> None:
        self._capsys = capsys

    def run(self, *args: str) -> tuple[int, str, str]:
        self._capsys.readouterr()
        code = main([*args, "--no-color"])
        captured = self._capsys.readouterr()
        return code, captured.out, captured.err

    def json(self, *args: str) -> tuple[int, dict]:
        code, out, _ = self.run(*args, "--json")
        return code, (json.loads(out) if out.strip() else {})


@pytest.fixture
def cli(capsys: pytest.CaptureFixture[str]) -> Runner:
    return Runner(capsys)


def test_scan_lists_candidates_as_a_dry_run(cli: Runner, project: Path) -> None:
    code, data = cli.json("scan", "--no-git-check", str(project))
    assert code == EXIT_OK
    assert data["dry_run"] is True
    assert [c["path"] for c in data["candidates"]] == ["out"]
    assert (project / "out" / "artifact.bin").exists()


def test_scan_quiet_prints_a_single_hint(cli: Runner, project: Path) -> None:
    code, out, _ = cli.run("scan", "--quiet", "--no-git-check", str(project))
    assert code == EXIT_OK
    assert "1 cleanup candidate(s)" in out and "sweepito scan" in out


def test_scan_outside_git_is_refused(cli: Runner, project: Path) -> None:
    code, _, err = cli.run("scan", str(project))
    assert code == EXIT_REFUSED
    assert "not inside a Git repository" in err


def test_check_fails_only_when_candidates_exist(
    cli: Runner, project: Path, tmp_path: Path
) -> None:
    code, _, _ = cli.run("check", "--quiet", "--no-git-check", str(project))
    assert code == EXIT_FAILED
    empty = tmp_path / "empty"
    empty.mkdir()
    code, _, _ = cli.run("check", "--quiet", "--no-git-check", str(empty))
    assert code == EXIT_OK


def test_clean_dry_run_deletes_nothing(cli: Runner, project: Path) -> None:
    code, data = cli.json("clean", "--dry-run", "--no-git-check", str(project))
    assert code == EXIT_OK and data["dry_run"] is True
    assert (project / "out").exists()


def test_clean_with_consent_removes_candidates_only(cli: Runner, project: Path) -> None:
    code, data = cli.json("clean", "--yes", "--no-git-check", str(project))
    assert code == EXIT_OK
    assert data["dry_run"] is False
    assert [c["path"] for c in data["removed"]] == ["out"]
    assert data["freed_bytes"] >= 100
    assert not (project / "out").exists()
    assert (project / "keep.txt").exists()


def test_clean_with_nothing_to_remove(cli: Runner, project: Path) -> None:
    cli.run("clean", "--yes", "--no-git-check", str(project))
    code, data = cli.json("clean", "--yes", "--no-git-check", str(project))
    assert code == EXIT_OK
    assert data["removed"] == [] and data["freed_bytes"] == 0


def test_clean_without_a_terminal_requires_consent(cli: Runner, project: Path) -> None:
    code, _, err = cli.run("clean", "--no-git-check", str(project))
    assert code == EXIT_REFUSED
    assert "--yes" in err
    assert (project / "out").exists()


def test_clean_non_interactive_proceeds(cli: Runner, project: Path) -> None:
    code, _, _ = cli.run("clean", "--non-interactive", "--no-git-check", str(project))
    assert code == EXIT_OK
    assert not (project / "out").exists()


def test_report_groups_reclaimable_space(cli: Runner, project: Path) -> None:
    code, data = cli.json("report", "--no-git-check", str(project))
    assert code == EXIT_OK
    assert data["total_bytes"] >= 100
    assert "custom.out" in data["rule"]
    assert data["rule"]["custom.out"]["risk"] == "custom"
    assert data["profile"]["custom"]["count"] == 1


def test_rules_lists_and_explains(cli: Runner, project: Path) -> None:
    code, data = cli.json("rules", str(project))
    assert code == EXIT_OK
    rules = {r["id"]: r for r in data["rules"]}
    assert rules["custom.out"]["default"] is True
    code, detail = cli.json("rules", "--explain", "custom.out", str(project))
    assert code == EXIT_OK
    assert detail["id"] == "custom.out" and detail["paths"] == ["out/"]


def test_rules_filters_by_profile_and_risk(cli: Runner, project: Path) -> None:
    _, data = cli.json("rules", "-p", "custom", str(project))
    assert [r["id"] for r in data["rules"]] == ["custom.out"]
    _, data = cli.json("rules", "--risk", "custom", str(project))
    assert [r["id"] for r in data["rules"]] == ["custom.out"]


def test_rules_unknown_id_is_a_usage_error(cli: Runner, project: Path) -> None:
    code, _, err = cli.run("rules", "--explain", "nope", str(project))
    assert code == EXIT_USAGE
    assert "Unknown rule ID" in err


def test_profiles_lists_and_explains(cli: Runner, project: Path) -> None:
    code, data = cli.json("profiles", str(project))
    assert code == EXIT_OK
    ids = {p["id"] for p in data["profiles"]}
    assert {"custom", "python"} <= ids
    code, detail = cli.json("profiles", "--explain", "custom", str(project))
    assert code == EXIT_OK
    assert [r["id"] for r in detail["rules"]] == ["custom.out"]


def test_profiles_unknown_name_is_a_usage_error(cli: Runner, project: Path) -> None:
    code, _, err = cli.run("profiles", "--explain", "nope", str(project))
    assert code == EXIT_USAGE
    assert "Unknown profile" in err


def test_config_validate_and_show(cli: Runner, project: Path) -> None:
    code, data = cli.json("config", "validate", str(project))
    assert code == EXIT_OK and data == {"valid": True}
    code, data = cli.json("config", "show", str(project))
    assert code == EXIT_OK
    assert data["config_file"].endswith("sweepito.toml")
    assert data["custom_rules"] == ["custom.out"]
    assert data["settings"]["risk"] == "safe"


def test_config_validate_rejects_a_broken_file(cli: Runner, tmp_path: Path) -> None:
    (tmp_path / "sweepito.toml").write_text("[nope]\n", encoding="utf-8")
    code, _, err = cli.run("config", "validate", str(tmp_path))
    assert code == EXIT_USAGE
    assert "Unknown section" in err


def test_init_writes_a_starter_file_and_protects_an_existing_one(
    cli: Runner, tmp_path: Path
) -> None:
    code, _, _ = cli.run("init", str(tmp_path))
    assert code == EXIT_OK
    target = tmp_path / "sweepito.toml"
    assert "[defaults]" in target.read_text(encoding="utf-8")
    code, _, err = cli.run("init", str(tmp_path))
    assert code == EXIT_REFUSED and "already exists" in err
    target.write_text("# mine\n", encoding="utf-8")
    code, _, _ = cli.run("init", "--force", str(tmp_path))
    assert code == EXIT_OK
    assert "# mine" not in target.read_text(encoding="utf-8")


def test_hook_needs_a_git_repository(cli: Runner, tmp_path: Path) -> None:
    code, _, err = cli.run("hook", "install", str(tmp_path))
    assert code == EXIT_REFUSED
    assert "Hooks need a Git repository" in err


def test_doctor_reports_every_check(cli: Runner, tmp_path: Path) -> None:
    code, data = cli.json("doctor", str(tmp_path))
    assert code in (EXIT_OK, EXIT_FAILED)
    assert data["healthy"] is (code == EXIT_OK)
    names = {c["name"] for c in data["checks"]}
    assert {"Sweepito", "Python", "Git", "Project root"} <= names
