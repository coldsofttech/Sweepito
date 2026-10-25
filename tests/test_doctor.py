from __future__ import annotations

import json

from sweepito.doctor import Check, passed
from tests.conftest import Repo


def checks_by_name(repo: Repo, *args: str) -> tuple[int, dict]:
    code, data = repo.json("doctor", *args)
    return code, {c["name"]: c for c in data["checks"]}


def test_doctor_renders_a_rich_table(repo: Repo) -> None:
    code, out, _ = repo.run("doctor", str(repo.root))
    assert code == 0
    assert "Sweepito doctor" in out
    for label in ("Check", "Result", "Details", "Python", "Git", "OK"):
        assert label in out


def test_doctor_json_reports_every_check(repo: Repo) -> None:
    code, data = repo.json("doctor")
    assert code == 0 and data["healthy"] is True
    names = [c["name"] for c in data["checks"]]
    for expected in ("Sweepito", "Python", "Git", "Configuration", "Profiles"):
        assert expected in names
    assert all(set(c) == {"name", "ok", "detail", "required"} for c in data["checks"])


def test_missing_hooks_are_optional_so_doctor_still_passes(repo: Repo) -> None:
    code, checks = checks_by_name(repo)
    assert code == 0
    assert checks["post-commit hook"]["ok"] is False
    assert checks["post-commit hook"]["required"] is False
    repo.run("hook", "install", str(repo.root))
    _, checks = checks_by_name(repo)
    assert checks["post-commit hook"]["ok"] is True


def test_invalid_config_fails_doctor_without_crashing(repo: Repo) -> None:
    repo.write("sweepito.toml", "[clean]\nbogus = 1\n")
    code, checks = checks_by_name(repo)
    assert code == 1
    assert checks["Configuration"]["ok"] is False
    assert "bogus" in checks["Configuration"]["detail"]
    code, out, _ = repo.run("doctor", str(repo.root))
    assert code == 1 and "FAILED" in out


def test_outside_git_is_reported_not_fatal(tmp_path, capsys) -> None:
    from sweepito.cli import main

    assert main(["doctor", str(tmp_path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    repo_check = next(c for c in data["checks"] if c["name"] == "Git repository")
    assert repo_check["ok"] is False and repo_check["required"] is False


def test_passed_only_considers_required_checks() -> None:
    assert passed([Check("a", True, ""), Check("b", False, "", required=False)])
    assert not passed([Check("a", False, "", required=True)])
