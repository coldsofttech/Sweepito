"""Every command renders through Rich; --json stays plain and parseable."""

from __future__ import annotations

import json

from tests.conftest import Repo


def project(repo: Repo) -> None:
    repo.write("pyproject.toml", "[project]\nname='x'\n")
    repo.write("Cargo.toml", "[package]\nname='x'\n")
    repo.write(".gitignore", "__pycache__/\n/target/\n")
    repo.write("src/__pycache__/a.pyc", "bytecode")
    repo.write("target/debug/app", "built")


def test_scan_renders_a_titled_table(repo: Repo) -> None:
    project(repo)
    code, out, _ = repo.run("scan", str(repo.root))
    assert code == 0
    for text in (
        "Cleanup candidates",
        "Rule",
        "Path",
        "Size",
        "Risk",
        "python.pycache",
    ):
        assert text in out
    assert "┌" in out or "+-" in out  # a bordered Rich table


def test_report_renders_one_table_per_grouping(repo: Repo) -> None:
    project(repo)
    code, out, _ = repo.run("report", str(repo.root))
    assert code == 0
    for title in ("By profile", "By rule", "By risk", "Total reclaimable"):
        assert title in out
    assert "rust.target" in out  # report covers every risk level
    rule_table = out.split("By rule")[1].split("By risk")[0]
    header = next(line for line in rule_table.splitlines() if "Rule" in line)
    columns = [c.strip() for c in header.strip("│| ").replace("│", "|").split("|")]
    assert columns == ["Rule", "Items", "Risk", "Size"]
    row = next(line for line in rule_table.splitlines() if "rust.target" in line)
    assert "configurable" in row


def test_rules_table_and_detail_panel(repo: Repo) -> None:
    repo.write("README.md", "x")
    _, out, _ = repo.run("rules", "-p", "rust", str(repo.root))
    assert "Sweepito rules" in out and "rust.target" in out and "opt-in" in out
    _, out, _ = repo.run("rules", "--explain", "node.next", str(repo.root))
    assert "Rule node.next" in out and "next.config.*" in out


def test_config_show_panel_and_json(repo: Repo) -> None:
    repo.write("sweepito.toml", '[clean]\nenable = ["rust.target"]\n')
    _, out, _ = repo.run("config", "show", str(repo.root))
    assert "Sweepito configuration" in out and "rust.target" in out
    code, data = repo.json("config", "show")
    assert code == 0 and data["settings"]["enable"] == ["rust.target"]


def test_hook_status_table(repo: Repo) -> None:
    _, out, _ = repo.run("hook", "status", str(repo.root))
    assert "Sweepito hooks" in out and "not installed" in out
    repo.run("hook", "install", str(repo.root))
    _, out, _ = repo.run("hook", "status", str(repo.root))
    assert "installed" in out and "post-commit" in out


def test_errors_go_to_stderr_with_a_consistent_prefix(repo: Repo) -> None:
    repo.write("README.md", "x")
    code, out, err = repo.run("scan", "--enable", "nope.nope", str(repo.root))
    assert code == 2 and out == ""
    assert err.startswith("sweepito: error: Unknown rule ID")


def test_json_output_is_plain_and_parseable(repo: Repo) -> None:
    project(repo)
    for args in (("scan",), ("report",), ("rules",), ("doctor",), ("hook", "status")):
        code, out, _ = repo.run(*args, "--json", str(repo.root))
        assert code == 0, args
        json.loads(out)  # no Rich markup, borders or ANSI codes
        assert "\x1b[" not in out and "┌" not in out


def test_profiles_table_lists_every_profile(repo: Repo) -> None:
    from sweepito.registry import Registry

    repo.write("README.md", "x")
    code, out, _ = repo.run("profiles", str(repo.root))
    assert code == 0
    for header in ("Sweepito profiles", "Profile", "Rules", "Configurable"):
        assert header in out
    for profile in Registry.build().profiles:
        assert profile in out


def test_profiles_json_counts_match_the_registry(repo: Repo) -> None:
    from sweepito.registry import Registry

    registry = Registry.build()
    repo.write("README.md", "x")
    code, out, _ = repo.run("profiles", "--json", str(repo.root))
    assert code == 0
    listed = {p["id"]: p for p in json.loads(out)["profiles"]}
    assert set(listed) == set(registry.profiles)
    rust = listed["rust"]
    assert rust["markers"] == ["Cargo.toml"] and rust["always_active"] is False
    assert (rust["rules"], rust["safe"], rust["configurable"]) == (2, 0, 2)
    assert listed["common"]["always_active"] is True
    for profile in registry.profiles.values():
        entry = listed[profile.id]
        assert entry["safe"] + entry["configurable"] + entry["high_impact"] == len(
            profile.rules
        )


def test_profiles_explain_shows_the_profile_and_its_rules(repo: Repo) -> None:
    repo.write("README.md", "x")
    code, out, _ = repo.run("profiles", "--explain", "rust", str(repo.root))
    assert code == 0
    for text in ("Profile rust", "Cargo.toml", "rust.target", "rust.profiling"):
        assert text in out
    code, out, _ = repo.run("profiles", "--explain", "rust", "--json", str(repo.root))
    assert [r["id"] for r in json.loads(out)["rules"]] == [
        "rust.target",
        "rust.profiling",
    ]


def test_profiles_unknown_name_is_a_usage_error(repo: Repo) -> None:
    repo.write("README.md", "x")
    code, out, err = repo.run("profiles", "--explain", "nope", str(repo.root))
    assert code == 2 and out == ""
    assert err.startswith("sweepito: error: Unknown profile")


def test_profiles_include_custom_profiles_from_config(repo: Repo) -> None:
    repo.write("sweepito.toml", '[profile.team]\nmarkers = ["team.marker"]\n')
    code, out, _ = repo.run("profiles", "--json", str(repo.root))
    team = next(p for p in json.loads(out)["profiles"] if p["id"] == "team")
    assert code == 0 and team["markers"] == ["team.marker"]
