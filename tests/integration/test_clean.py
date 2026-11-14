from __future__ import annotations

import os

import pytest

from tests.conftest import Repo


def python_project(repo: Repo) -> None:
    repo.write("pyproject.toml", "[project]\nname='x'\n")
    repo.write(".gitignore", "__pycache__/\n*.pyc\n.pytest_cache/\nbuild/\n.venv/\n")
    repo.write("src/app.py", "print('hi')")
    repo.write("src/__pycache__/app.cpython-312.pyc", "bytecode")
    repo.write(".pytest_cache/README.md", "cache")
    repo.git("add", "pyproject.toml", ".gitignore", "src/app.py")


def test_safe_rules_are_default_and_dry_run_deletes_nothing(repo: Repo) -> None:
    python_project(repo)
    found = repo.candidates()
    assert found == {
        "src/__pycache__": "python.pycache",
        ".pytest_cache": "python.pytest",
    }
    code, _, _ = repo.run("clean", "--dry-run", str(repo.root))
    assert code == 0
    assert repo.exists("src/__pycache__/app.cpython-312.pyc")


def test_clean_removes_candidates_and_keeps_source(repo: Repo) -> None:
    python_project(repo)
    code, data = repo.json("clean", "--yes")
    assert code == 0
    assert len(data["removed"]) == 2
    assert not repo.exists("src/__pycache__")
    assert not repo.exists(".pytest_cache")
    assert repo.exists("src/app.py")


def test_total_bytes_reported(repo: Repo) -> None:
    python_project(repo)
    _, data = repo.json("scan")
    assert data["total_bytes"] == len("bytecode") + len("cache")


def test_configurable_rules_are_opt_in(repo: Repo) -> None:
    python_project(repo)
    repo.write("build/out.bin", "data")
    assert "build" not in repo.candidates()
    assert repo.candidates("--risk", "configurable")["build"] == "python.build"
    assert repo.candidates("--enable", "python.build")["build"] == "python.build"


def test_generic_name_needs_marker(repo: Repo) -> None:
    repo.write(".gitignore", "build/\n")
    repo.write("build/out.bin", "data")
    repo.write("README.md", "hello")
    assert repo.candidates("--risk", "configurable") == {}


def test_tracked_paths_are_never_deleted(repo: Repo) -> None:
    python_project(repo)
    repo.write("keep/__pycache__/x.pyc", "tracked")
    repo.git("add", "-f", "keep/__pycache__/x.pyc")
    _, data = repo.json("scan")
    assert "keep/__pycache__" not in {c["path"] for c in data["candidates"]}
    repo.json("clean", "--yes")
    assert repo.exists("keep/__pycache__/x.pyc")


def test_tracked_content_in_anchored_target_is_reported_and_kept(repo: Repo) -> None:
    repo.write("Cargo.toml", "[package]\nname='x'\n")
    repo.write(".gitignore", "target/\n")
    repo.write("target/debug/a", "built")
    repo.write("target/committed.txt", "keep")
    repo.git("add", "-f", "target/committed.txt")
    _, data = repo.json("scan", "--enable", "rust.target")
    assert data["candidates"] == []
    assert [s["reason"] for s in data["skipped"]] == ["tracked by git"]
    repo.json("clean", "--yes", "--enable", "rust.target")
    assert repo.exists("target/committed.txt") and repo.exists("target/debug/a")


def test_paths_not_ignored_by_git_are_never_listed(repo: Repo) -> None:
    repo.write("pyproject.toml", "[project]\nname='x'\n")
    repo.write("pkg/__pycache__/a.pyc", "not ignored")
    _, data = repo.json("scan")
    assert data["candidates"] == []
    repo.json("clean", "--yes")
    assert repo.exists("pkg/__pycache__/a.pyc")


def test_high_impact_rules_are_opt_in_but_need_no_extra_flag(repo: Repo) -> None:
    repo.write("package.json", "{}")
    repo.write(".gitignore", "node_modules/\n")
    repo.write("node_modules/pkg/index.js", "x")
    assert repo.candidates() == {}  # never selected by default
    assert repo.candidates("--risk", "configurable") == {}
    for args in (("--enable", "node.modules"), ("--risk", "high-impact")):
        found = repo.candidates(*args)
        assert found["node_modules"] == "node.modules", args
        # node_modules/.cache is covered by the parent and not listed twice
        assert "node_modules/.cache" not in found
    code, data = repo.json("clean", "--yes", "--enable", "node.modules")
    assert code == 0 and not repo.exists("node_modules")


def test_allow_high_impact_flag_no_longer_exists(repo: Repo) -> None:
    repo.write("README.md", "x")
    with pytest.raises(SystemExit) as exc:  # argparse rejects unknown options
        repo.run("scan", "--allow-high-impact", str(repo.root))
    assert exc.value.code == 2


def test_exclude_patterns_always_win(repo: Repo) -> None:
    python_project(repo)
    assert ".pytest_cache" not in repo.candidates("--exclude", ".pytest_cache/")
    assert repo.candidates("--exclude", "src/")  # only .pytest_cache remains


def test_nested_projects_use_their_own_markers(repo: Repo) -> None:
    repo.write("web/package.json", "{}")
    repo.write("web/next.config.js", "module.exports = {}")
    repo.write("api/package.json", "{}")
    repo.write(".gitignore", ".next/\n")
    repo.write("web/.next/cache/a", "1")
    repo.write("api/.next/cache/a", "1")  # no next.config in api -> not a Next.js app
    found = repo.candidates("--risk", "configurable")
    assert found == {"web/.next": "node.next"}


def test_literal_cache_inside_dependency_dir(repo: Repo) -> None:
    repo.write("package.json", "{}")
    repo.write(".gitignore", "node_modules/\n")
    repo.write("node_modules/.cache/babel/x", "1")
    repo.write("node_modules/pkg/index.js", "1")
    found = repo.candidates()
    assert found == {"node_modules/.cache": "node.modules-cache"}
    repo.json("clean", "--yes")
    assert repo.exists("node_modules/pkg/index.js")


def test_symlinks_are_removed_as_links_not_followed(repo: Repo, tmp_path) -> None:
    python_project(repo)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("keep me")
    link = repo.root / "link.pyc"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this system")
    assert "link.pyc" in repo.candidates()
    repo.json("clean", "--yes")
    assert not repo.exists("link.pyc")
    assert (outside / "precious.txt").read_text() == "keep me"


def test_outside_git_is_refused_unless_forced(tmp_path, capsys) -> None:
    plain = tmp_path / "plain"
    (plain / "__pycache__").mkdir(parents=True)
    (plain / "pyproject.toml").write_text("[project]\nname='x'\n")
    (plain / "__pycache__" / "a.pyc").write_text("x")
    from sweepito.cli import main

    assert main(["scan", str(plain), "--json"]) == 4
    capsys.readouterr()
    assert main(["scan", str(plain), "--json", "--no-git-check"]) == 0


def test_clean_without_terminal_requires_consent(repo: Repo) -> None:
    python_project(repo)
    code, _, err = repo.run("clean", str(repo.root))
    assert code == 4
    assert "--yes" in err
    assert repo.exists("src/__pycache__")


def test_check_exit_codes(repo: Repo) -> None:
    python_project(repo)
    assert repo.run("check", "--quiet", str(repo.root))[0] == 1
    repo.json("clean", "--yes")
    assert repo.run("check", "--quiet", str(repo.root))[0] == 0


def test_quiet_is_silent_when_nothing_to_do(repo: Repo) -> None:
    repo.write("README.md", "hi")
    code, out, err = repo.run("clean", "--non-interactive", "--quiet", str(repo.root))
    assert (code, out, err) == (0, "", "")


def test_unknown_rule_and_profile_are_usage_errors(repo: Repo) -> None:
    repo.write("README.md", "hi")
    assert repo.run("scan", "--enable", "nope.nope", str(repo.root))[0] == 2
    assert repo.run("scan", "-p", "nope", str(repo.root))[0] == 2


@pytest.mark.parametrize("stage", ["post-commit", "pre-commit"])
def test_hook_install_is_idempotent_and_preserves_content(
    repo: Repo, stage: str
) -> None:
    hook = repo.root / ".git" / "hooks" / stage
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho existing\n")
    for _ in range(2):
        assert repo.run("hook", "install", "--stage", stage, str(repo.root))[0] == 0
    text = hook.read_text()
    assert "echo existing" in text
    assert text.count("# >>> sweepito >>>") == 1
    assert repo.run("hook", "uninstall", "--stage", stage, str(repo.root))[0] == 0
    assert "sweepito" not in hook.read_text()
    assert "echo existing" in hook.read_text()


def test_hook_uninstall_removes_file_we_created(repo: Repo) -> None:
    repo.run("hook", "install", str(repo.root))
    hook = repo.root / ".git" / "hooks" / "post-commit"
    assert hook.exists()
    repo.run("hook", "uninstall", str(repo.root))
    assert not hook.exists()


def test_confirmation_prompt_without_input_is_a_refusal_not_a_crash(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    python_project(repo)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)

    def no_input(_prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", no_input)
    code, _, err = repo.run("clean", str(repo.root))
    assert code == 4
    assert "--yes" in err
    assert repo.exists("src/__pycache__")


def test_declining_the_prompt_deletes_nothing(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    python_project(repo)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    code, out, _ = repo.run("clean", str(repo.root))
    assert code == 0
    assert "Aborted" in out
    assert repo.exists("src/__pycache__")
