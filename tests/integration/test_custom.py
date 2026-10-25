"""Integration tests: sample custom rules, end to end through the command line.

Each ``Sample`` is a realistic ``sweepito.toml`` with the files a project would have.
The suite checks that the right paths are found, that ``clean`` removes exactly those
and nothing else, and that the built-in safety gates still apply to user-defined rules.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest

from tests.conftest import Repo


def toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(v) for v in value) + "]"
    return json.dumps(value)  # a quoted string; JSON and TOML agree for these values


def rule(rule_id: str, paths: list[str], **extra: object) -> str:
    lines = ["[[rule]]", f"id = {toml_value(rule_id)}", f"paths = {toml_value(paths)}"]
    lines += [f"{key} = {toml_value(value)}" for key, value in extra.items()]
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class Sample:
    id: str
    toml: str
    files: dict[str, str]  # everything that exists in the project
    expected: dict[str, str]  # candidate path -> rule id
    ignore: tuple[str, ...] = ()  # .gitignore lines
    tracked: tuple[str, ...] = ()  # files force-added to git
    args: tuple[str, ...] = field(default=())  # extra command line options


SAMPLES = [
    Sample(
        "minimal",
        rule("custom.test-output", ["test-results/"]),
        {"test-results/a.xml": "1", "src/app.py": "code"},
        {"test-results": "custom.test-output"},
        ignore=("test-results/",),
    ),
    Sample(
        "anchored-and-anywhere",
        rule("custom.e2e", ["/tmp/e2e/", "snapshots/"]),
        {
            "tmp/e2e/run.log": "1",
            "tmp/other/keep.log": "1",
            "snapshots/a": "1",
            "web/snapshots/b": "1",
            "src/app.py": "code",
        },
        {
            "tmp/e2e": "custom.e2e",
            "snapshots": "custom.e2e",
            "web/snapshots": "custom.e2e",
        },
        ignore=("/tmp/", "snapshots/"),
    ),
    Sample(
        "file-patterns",
        rule("custom.generated", ["*.generated.ts"]),
        {
            "api.generated.ts": "1",
            "src/db.generated.ts": "1",
            "src/keep.ts": "code",
        },
        {
            "api.generated.ts": "custom.generated",
            "src/db.generated.ts": "custom.generated",
        },
        ignore=("*.generated.ts",),
    ),
    Sample(
        "marker-gated",
        rule("custom.cpp-builds", ["/build-*/"], requires=["CMakeLists.txt"]),
        {
            "CMakeLists.txt": "",
            "build-debug/a": "1",
            "build-release/a": "1",
            "tools/build-debug/a": "1",  # no CMakeLists.txt in tools/
        },
        {"build-debug": "custom.cpp-builds", "build-release": "custom.cpp-builds"},
        ignore=("build-*/",),
    ),
    Sample(
        "nested-project-marker",
        rule("custom.storybook", ["/storybook-static/"], requires=["package.json"]),
        {
            "web/package.json": "{}",
            "web/storybook-static/a": "1",
            "api/storybook-static/a": "1",  # api/ has no package.json
        },
        {"web/storybook-static": "custom.storybook"},
        ignore=("storybook-static/",),
    ),
    Sample(
        "not-ignored-needs-allow-untracked",
        rule("custom.scratch", ["/scratch/", ".test/"], allow_untracked=True),
        {"scratch/a": "1", "pkg/.test/b": "1", "src/app.py": "code"},
        {"scratch": "custom.scratch", "pkg/.test": "custom.scratch"},
    ),
    Sample(
        "not-ignored-without-the-flag-is-left-alone",
        rule("custom.scratch", ["/scratch/", ".test/"]),
        {"scratch/a": "1", "pkg/.test/b": "1"},
        {},
    ),
    Sample(
        "tracked-content-survives-allow-untracked",
        rule("custom.scratch", [".test/"], allow_untracked=True),
        {".test/keep": "tracked", ".test/scratch": "untracked"},
        {".test/scratch": "custom.scratch"},
        tracked=(".test/keep",),
    ),
    Sample(
        "two-rules",
        rule("custom.a", ["/out-a/"]) + "\n" + rule("custom.b", ["/out-b/"]),
        {"out-a/x": "1", "out-b/x": "1", "out-c/x": "1"},
        {"out-a": "custom.a", "out-b": "custom.b"},
        ignore=("out-*/",),
    ),
    Sample(
        "alongside-builtin-rules",
        rule("custom.test-output", ["test-results/"]),
        {
            "pyproject.toml": "[project]\nname='x'\n",
            "src/__pycache__/a.pyc": "1",
            "test-results/a.xml": "1",
        },
        {"src/__pycache__": "python.pycache", "test-results": "custom.test-output"},
        ignore=("__pycache__/", "test-results/"),
    ),
]


def build(repo: Repo, sample: Sample) -> None:
    repo.write("sweepito.toml", sample.toml)
    for name, content in sample.files.items():
        repo.write(name, content)
    if sample.ignore:
        repo.write(".gitignore", "\n".join(sample.ignore) + "\n")
    for name in sample.tracked:
        repo.git("add", "-f", name)


@pytest.mark.parametrize("sample", SAMPLES, ids=[s.id for s in SAMPLES])
def test_sample_finds_exactly_the_expected_paths(repo: Repo, sample: Sample) -> None:
    build(repo, sample)
    assert repo.candidates(*sample.args) == sample.expected


@pytest.mark.parametrize("sample", SAMPLES, ids=[s.id for s in SAMPLES])
def test_sample_clean_removes_those_paths_and_nothing_else(
    repo: Repo, sample: Sample
) -> None:
    build(repo, sample)
    before = {p.relative_to(repo.root).as_posix() for p in repo.root.rglob("*")}
    code, data = repo.json("clean", "--yes", *sample.args)
    assert code == 0 and data["failed"] == []
    assert {c["path"] for c in data["removed"]} == set(sample.expected)
    for path in sample.expected:
        assert not repo.exists(path), path
    # every file that was not under a removed path is still there
    removed = tuple(sample.expected)
    survivors = {
        name
        for name in sample.files
        if not any(name == r or name.startswith(r + "/") for r in removed)
    }
    for name in survivors:
        assert repo.exists(name), f"{name} was removed"
    assert repo.exists("sweepito.toml")
    assert before  # sanity: the project was not empty


@pytest.mark.parametrize("sample", SAMPLES, ids=[s.id for s in SAMPLES])
def test_sample_second_run_finds_nothing(repo: Repo, sample: Sample) -> None:
    build(repo, sample)
    repo.json("clean", "--yes", *sample.args)
    assert repo.candidates(*sample.args) == {}


# ---- behaviour that applies to every custom rule ---------------------------------


def minimal_project(repo: Repo, toml: str, ignored: str = "out/") -> None:
    repo.write("sweepito.toml", toml)
    repo.write(".gitignore", ignored + "\n")
    repo.write("out/a", "1")


def test_custom_rule_without_risk_runs_by_default_and_is_labelled_custom(
    repo: Repo,
) -> None:
    minimal_project(repo, rule("custom.out", ["out/"]))
    code, data = repo.json("scan")  # no --risk, no --enable
    assert code == 0
    [candidate] = data["candidates"]
    assert (candidate["rule"], candidate["risk"]) == ("custom.out", "custom")
    assert candidate["profile"] == "custom"


@pytest.mark.parametrize("risk", ["custom", "safe", "configurable", "high-impact"])
def test_custom_rules_reject_a_risk_setting(repo: Repo, risk: str) -> None:
    minimal_project(repo, rule("custom.out", ["out/"], risk=risk))
    code, _, err = repo.run("scan", str(repo.root))
    assert code == 2
    assert "custom rules do not take a 'risk' level" in err


def test_custom_rules_always_run_whatever_the_risk_ceiling(repo: Repo) -> None:
    minimal_project(repo, rule("custom.out", ["out/"]))
    for args in ((), ("--risk", "safe"), ("--risk", "configurable")):
        assert repo.candidates(*args) == {"out": "custom.out"}, args
    assert repo.candidates("--risk", "high-impact") == {"out": "custom.out"}


def test_disable_and_exclude_beat_a_custom_rule(repo: Repo) -> None:
    minimal_project(repo, rule("custom.out", ["out/"]))
    assert repo.candidates("--disable", "custom.out") == {}
    assert repo.candidates("--exclude", "out/") == {}
    assert repo.candidates() == {"out": "custom.out"}


def test_config_can_disable_its_own_custom_rule(repo: Repo) -> None:
    minimal_project(
        repo, rule("custom.out", ["out/"]) + '\n[clean]\ndisable = ["custom.out"]\n'
    )
    assert repo.candidates() == {}


def test_custom_profile_with_markers_gates_its_rules(repo: Repo) -> None:
    toml = (
        '[profile.team]\nmarkers = ["team.marker"]\n\n'
        + rule("team.out", ["/out/"], profile="team")
        + "\n"
        + rule("custom.always", ["/always/"])
    )
    minimal_project(repo, toml, ignored="out/\nalways/")
    repo.write("always/a", "1")
    assert repo.candidates() == {"always": "custom.always"}  # team is inactive
    repo.write("team.marker", "")
    assert repo.candidates() == {"always": "custom.always", "out": "team.out"}
    assert repo.candidates("-p", "team") == {"out": "team.out"}


def test_custom_rules_are_listed_and_explained(repo: Repo) -> None:
    minimal_project(
        repo,
        rule(
            "custom.out",
            ["/out/"],
            requires=["package.json"],
            description="Build output",
        ),
    )
    _, out, _ = repo.run("rules", "-p", "custom", "--json", str(repo.root))
    [listed] = json.loads(out)["rules"]
    assert listed["id"] == "custom.out" and listed["risk"] == "custom"
    assert listed["default"] is True
    _, out, _ = repo.run("rules", "--explain", "custom.out", "--json", str(repo.root))
    details = json.loads(out)
    assert details["requires"] == ["package.json"]
    assert details["description"] == "Build output"
    _, text, _ = repo.run("rules", "-p", "custom", str(repo.root))
    assert "custom.out" in text and "custom" in text


def test_custom_rules_show_in_the_profiles_listing(repo: Repo) -> None:
    minimal_project(repo, rule("custom.out", ["out/"]))
    _, out, _ = repo.run("profiles", "--json", str(repo.root))
    custom = next(p for p in json.loads(out)["profiles"] if p["id"] == "custom")
    assert (custom["rules"], custom["custom"]) == (1, 1)
    assert custom["always_active"] is True


def test_report_includes_custom_rules_with_their_risk(repo: Repo) -> None:
    minimal_project(repo, rule("custom.out", ["out/"]))
    _, out, _ = repo.run("report", "--json", str(repo.root))
    data = json.loads(out)
    assert data["rule"]["custom.out"]["risk"] == "custom"
    assert "custom" in data["risk"]


def test_doctor_and_config_show_see_custom_rules(repo: Repo) -> None:
    minimal_project(repo, rule("custom.out", ["out/"]))
    _, out, _ = repo.run("config", "show", "--json", str(repo.root))
    assert json.loads(out)["custom_rules"] == ["custom.out"]
    code, _, _ = repo.run("config", "validate", str(repo.root))
    assert code == 0


def test_a_custom_rule_never_leaves_the_project(repo: Repo, tmp_path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("keep")
    for bad in ("../outside/", "/../outside/", "C:/outside/", "~/outside/"):
        repo.write("sweepito.toml", rule("custom.bad", [bad]))
        code, _, err = repo.run("scan", str(repo.root))
        assert code == 2 and "Unsafe or invalid path pattern" in err, bad
    assert (outside / "precious.txt").read_text() == "keep"


def test_exec_rules_are_rejected(repo: Repo) -> None:
    repo.write(
        "sweepito.toml", '[[rule]]\nid = "custom.run"\nexec = ["rm", "-rf", "."]\n'
    )
    code, _, err = repo.run("scan", str(repo.root))
    assert code == 2 and "exec" in err


def test_custom_rule_cannot_reuse_a_builtin_id(repo: Repo) -> None:
    repo.write("sweepito.toml", rule("python.pycache", ["out/"]))
    assert repo.run("scan", str(repo.root))[0] == 2


def test_custom_rule_cannot_delete_dot_git_even_if_asked(repo: Repo) -> None:
    repo.write("sweepito.toml", rule("custom.git", ["/.git/"], allow_untracked=True))
    repo.write("README.md", "x")
    repo.json("clean", "--yes")
    assert repo.exists(".git/HEAD")


def test_symlinks_are_removed_as_links_never_followed(repo: Repo, tmp_path) -> None:
    import os

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("keep")
    minimal_project(repo, rule("custom.links", ["*.link"]), ignored="*.link")
    try:
        os.symlink(outside, repo.root / "data.link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this system")
    assert repo.candidates() == {"data.link": "custom.links"}
    repo.json("clean", "--yes")
    assert not repo.exists("data.link")
    assert (outside / "precious.txt").read_text() == "keep"


def test_custom_rules_apply_from_a_pyproject_table(repo: Repo) -> None:
    repo.write(
        "pyproject.toml",
        '[project]\nname = "x"\n\n[[tool.sweepito.rule]]\n'
        'id = "custom.out"\npaths = ["out/"]\n',
    )
    repo.write(".gitignore", "out/\n")
    repo.write("out/a", "1")
    assert repo.candidates() == {"out": "custom.out"}


def test_hook_runs_apply_custom_rules_quietly(repo: Repo) -> None:
    minimal_project(repo, rule("custom.out", ["out/"]))
    code, out, err = repo.run(
        "clean", "--hook", "--non-interactive", "--quiet", str(repo.root)
    )
    assert (code, out, err) == (0, "", "")
    assert not repo.exists("out")


# ---- custom as a --risk value ----------------------------------------------------


def mixed_project(repo: Repo) -> None:
    """A Python project with a built-in cache and one custom rule's output."""
    repo.write("pyproject.toml", "[project]\nname='x'\n")
    repo.write("sweepito.toml", rule("custom.out", ["out/"]))
    repo.write(".gitignore", "__pycache__/\nout/\n")
    repo.write("src/__pycache__/a.pyc", "bytecode")
    repo.write("out/a", "1")


def test_risk_custom_selects_only_your_own_rules(repo: Repo) -> None:
    mixed_project(repo)
    assert repo.candidates() == {  # default: built-in safe rules plus custom
        "src/__pycache__": "python.pycache",
        "out": "custom.out",
    }
    assert repo.candidates("--risk", "custom") == {"out": "custom.out"}


def test_risk_custom_clean_leaves_built_in_targets_alone(repo: Repo) -> None:
    mixed_project(repo)
    code, data = repo.json("clean", "--yes", "--risk", "custom")
    assert code == 0 and [c["path"] for c in data["removed"]] == ["out"]
    assert repo.exists("src/__pycache__/a.pyc") and not repo.exists("out")


def test_risk_custom_can_be_combined_with_enable(repo: Repo) -> None:
    mixed_project(repo)
    found = repo.candidates("--risk", "custom", "--enable", "python.pycache")
    assert found == {"src/__pycache__": "python.pycache", "out": "custom.out"}


def test_risk_custom_as_the_default_in_config(repo: Repo) -> None:
    mixed_project(repo)
    repo.write(
        "sweepito.toml",
        rule("custom.out", ["out/"]) + '\n[defaults]\nrisk = "custom"\n',
    )
    assert repo.candidates() == {"out": "custom.out"}
    # the command line still wins over the file
    assert "src/__pycache__" in repo.candidates("--risk", "safe")


def test_hooks_can_be_limited_to_custom_rules(repo: Repo) -> None:
    mixed_project(repo)
    repo.write(
        "sweepito.toml", rule("custom.out", ["out/"]) + '\n[hook]\nrisk = "custom"\n'
    )
    code, out, err = repo.run(
        "clean", "--hook", "--non-interactive", "--quiet", str(repo.root)
    )
    assert (code, out, err) == (0, "", "")
    assert not repo.exists("out")
    assert repo.exists("src/__pycache__/a.pyc")  # built-in rules did not run


def test_rules_risk_custom_lists_only_custom_rules(repo: Repo) -> None:
    mixed_project(repo)
    _, out, _ = repo.run("rules", "--risk", "custom", "--json", str(repo.root))
    rules = json.loads(out)["rules"]
    assert [r["id"] for r in rules] == ["custom.out"]
    assert all(r["risk"] == "custom" and r["default"] for r in rules)


def test_rules_risk_custom_is_empty_without_custom_rules(repo: Repo) -> None:
    repo.write("README.md", "x")
    _, out, _ = repo.run("rules", "--risk", "custom", "--json", str(repo.root))
    assert json.loads(out) == {"rules": []}


def test_report_and_check_accept_risk_custom(repo: Repo) -> None:
    mixed_project(repo)
    assert repo.run("check", "--quiet", "--risk", "custom", str(repo.root))[0] == 1
    code, out, _ = repo.run("report", "--risk", "custom", "--json", str(repo.root))
    assert code == 0 and "custom.out" in json.loads(out)["rule"]
