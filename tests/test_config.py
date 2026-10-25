from __future__ import annotations

import json

import pathspec
import pytest

from sweepito.config import Options, load_config, merge, validate_pattern
from sweepito.errors import ConfigError
from sweepito.models import Risk
from sweepito.registry import Registry
from tests.conftest import Repo


def test_builtin_profiles_are_consistent() -> None:
    registry = Registry.build()
    assert len(registry.profiles) >= 17
    assert "common" in registry.profiles
    assert len(registry.rules) == sum(len(p.rules) for p in registry.profiles.values())
    for rule in registry.rules.values():
        assert rule.paths, rule.id
        for pattern in rule.paths:
            validate_pattern(pattern, rule.id)
            pathspec.GitIgnoreSpec.from_lines([pattern])
        assert rule.id.split(".")[0], rule.id


def test_config_files_are_validated(tmp_path) -> None:
    path = tmp_path / "sweepito.toml"
    path.write_text("[clean]\nbogus = 1\n")
    with pytest.raises(ConfigError, match="bogus"):
        load_config(path)
    path.write_text('[[rule]]\nid = "x.y"\npaths = ["../etc/"]\n')
    with pytest.raises(ConfigError, match="Unsafe"):
        load_config(path)
    path.write_text('[[rule]]\nid = "x.y"\nexec = ["rm", "-rf", "."]\n')
    with pytest.raises(ConfigError, match="exec"):
        load_config(path)
    path.write_text("not = [valid")
    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_config(path)
    path.write_text("[nonsense]\n")
    with pytest.raises(ConfigError, match="Unknown section"):
        load_config(path)


@pytest.mark.parametrize(
    "pattern", ["../x", "C:/x", "~/x", "!keep", "a\\b", "//srv/x", ""]
)
def test_unsafe_patterns_rejected(pattern: str) -> None:
    with pytest.raises(ConfigError):
        validate_pattern(pattern, "test")


def test_precedence_cli_over_file_and_lists_combine(tmp_path) -> None:
    path = tmp_path / "sweepito.toml"
    path.write_text(
        '[defaults]\nrisk = "configurable"\n'
        '[clean]\nenable = ["a.b"]\nexclude = ["dist/"]\n'
        '[hook]\nrisk = "safe"\nquiet = true\n'
    )
    cfg = load_config(path)
    assert merge(Options(), cfg).risk is Risk.CONFIGURABLE
    assert merge(Options(risk=Risk.SAFE), cfg).risk is Risk.SAFE
    hooked = merge(Options(hook=True), cfg)
    assert hooked.risk is Risk.SAFE and hooked.quiet
    combined = merge(Options(enable=("c.d",), exclude=("out/",)), cfg)
    assert combined.enable == ("a.b", "c.d")
    assert combined.exclude == ("dist/", "out/")


def test_pyproject_table_is_supported(repo: Repo) -> None:
    repo.write("pyproject.toml", '[tool.sweepito.defaults]\nrisk = "configurable"\n')
    repo.write(".gitignore", "build/\n")
    repo.write("build/x", "1")
    assert repo.candidates() == {"build": "python.build"}


def test_custom_path_rule(repo: Repo) -> None:
    repo.write(
        "sweepito.toml",
        '[[rule]]\nid = "custom.test-output"\npaths = ["test-results/", "/tmp/e2e/"]\n',
    )
    repo.write(".gitignore", "test-results/\ntmp/\n")
    repo.write("test-results/a.xml", "1")
    repo.write("tmp/e2e/a", "1")
    repo.write("tmp/other/a", "1")
    assert repo.candidates() == {
        "test-results": "custom.test-output",
        "tmp/e2e": "custom.test-output",
    }


def test_custom_rule_still_requires_git_ignore_unless_allowed(repo: Repo) -> None:
    repo.write(
        "sweepito.toml",
        '[[rule]]\nid = "custom.scratch"\npaths = ["/scratch/"]\n'
        '[[rule]]\nid = "custom.forced"\npaths = ["/forced/"]\n'
        "allow_untracked = true\n",
    )
    repo.write("scratch/a", "1")
    repo.write("forced/a", "1")
    repo.write("forced/tracked", "1")
    assert repo.candidates() == {"forced": "custom.forced"}
    repo.git("add", "forced/tracked")
    assert repo.candidates() == {}  # a tracked file inside protects the directory


def test_custom_profile_with_markers(repo: Repo) -> None:
    repo.write(
        "sweepito.toml",
        '[profile.team]\nmarkers = ["team.marker"]\n'
        '[[rule]]\nid = "team.out"\nprofile = "team"\n'
        'paths = ["/out/"]\n',
    )
    repo.write(".gitignore", "out/\n")
    repo.write("out/a", "1")
    assert repo.candidates() == {}
    repo.write("team.marker", "")
    assert repo.candidates() == {"out": "team.out"}


def test_duplicate_rule_ids_rejected(repo: Repo) -> None:
    repo.write("sweepito.toml", '[[rule]]\nid = "python.pycache"\npaths = ["x/"]\n')
    assert repo.run("scan", str(repo.root))[0] == 2


def test_disable_beats_enable(repo: Repo) -> None:
    repo.write("pyproject.toml", "[project]\nname='x'\n")
    repo.write(".gitignore", ".ruff_cache/\n")
    repo.write(".ruff_cache/a", "1")
    assert repo.candidates("--disable", "python.ruff", "--enable", "python.ruff") == {}


def test_explicit_config_flag(repo: Repo, tmp_path) -> None:
    other = tmp_path / "other.toml"
    other.write_text('[defaults]\nrisk = "configurable"\n')
    repo.write("pyproject.toml", "[project]\nname='x'\n")
    repo.write(".gitignore", "build/\n")
    repo.write("build/x", "1")
    assert repo.candidates() == {}
    assert repo.candidates("--config", str(other)) == {"build": "python.build"}
    assert (
        repo.run("scan", "--config", str(tmp_path / "missing.toml"), str(repo.root))[0]
        == 2
    )


def test_rules_and_config_commands(repo: Repo) -> None:
    repo.write("README.md", "hi")
    code, out, _ = repo.run("rules", "--json", str(repo.root))
    assert code == 0 and "python.pycache" in out
    code, out, _ = repo.run("rules", "--explain", "rust.target", str(repo.root))
    assert code == 0 and "/target/" in out
    assert repo.run("config", "validate", str(repo.root))[0] == 0
    assert repo.run("init", str(repo.root))[0] == 0
    assert (repo.root / "sweepito.toml").exists()
    assert repo.run("init", str(repo.root))[0] == 4  # refuses to overwrite
    assert repo.run("config", "show", str(repo.root))[0] == 0


def test_allow_untracked_works_with_unanchored_patterns(repo: Repo) -> None:
    repo.write(
        "sweepito.toml",
        '[[rule]]\nid = "custom.test"\npaths = [".test/"]\nallow_untracked = true\n',
    )
    repo.write(".test/a", "1")  # not in .gitignore
    repo.write("pkg/.test/b", "1")  # unanchored: matches at any depth
    assert repo.candidates() == {
        ".test": "custom.test",
        "pkg/.test": "custom.test",
    }
    repo.json("clean", "--yes")
    assert not repo.exists(".test") and not repo.exists("pkg/.test")


def test_allow_untracked_still_protects_tracked_content(repo: Repo) -> None:
    repo.write(
        "sweepito.toml",
        '[[rule]]\nid = "custom.test"\npaths = [".test/"]\nallow_untracked = true\n',
    )
    repo.write(".test/keep", "tracked")
    repo.write(".test/scratch", "untracked")
    repo.git("add", ".test/keep")
    found = repo.candidates()
    assert ".test" not in found  # the directory holds a tracked file
    assert found.get(".test/scratch") == "custom.test"
    repo.json("clean", "--yes")
    assert repo.exists(".test/keep") and not repo.exists(".test/scratch")


def test_unanchored_pattern_without_allow_untracked_ignores_unignored_dirs(
    repo: Repo,
) -> None:
    repo.write(
        "sweepito.toml",
        '[[rule]]\nid = "custom.test"\npaths = [".test/"]\n',
    )
    repo.write(".test/a", "1")
    assert repo.candidates() == {}


def test_custom_rule_without_risk_is_labelled_custom_and_runs_by_default(
    repo: Repo,
) -> None:
    repo.write(
        "sweepito.toml", '[[rule]]\nid = "custom.scratch"\npaths = ["/scratch/"]\n'
    )
    repo.write(".gitignore", "scratch/\n")
    repo.write("scratch/a", "1")
    code, data = repo.json("scan")  # default risk ceiling, no --enable
    assert code == 0
    [candidate] = data["candidates"]
    assert candidate["rule"] == "custom.scratch" and candidate["risk"] == "custom"
    repo.json("clean", "--yes")
    assert not repo.exists("scratch")


def test_custom_rules_do_not_take_a_risk_level(repo: Repo) -> None:
    repo.write(
        "sweepito.toml",
        '[[rule]]\nid = "custom.scratch"\npaths = ["/scratch/"]\n'
        'risk = "configurable"\n',
    )
    code, _, err = repo.run("config", "validate", str(repo.root))
    assert code == 2
    assert "custom rules do not take a 'risk' level" in err


def test_custom_is_a_valid_risk_level_everywhere(repo: Repo) -> None:
    repo.write(
        "sweepito.toml", '[defaults]\nrisk = "custom"\n[hook]\nrisk = "custom"\n'
    )
    assert repo.run("config", "validate", str(repo.root))[0] == 0
    cfg = load_config(repo.root / "sweepito.toml")
    assert cfg.risk is Risk.CUSTOM and cfg.hook_risk is Risk.CUSTOM
    assert merge(Options(), cfg).risk is Risk.CUSTOM
    assert Risk.parse("custom") is Risk.CUSTOM
    with pytest.raises(ConfigError, match="expected custom, safe"):
        Risk.parse("bogus")


def test_custom_rules_appear_in_rules_and_profiles_listings(repo: Repo) -> None:
    repo.write(
        "sweepito.toml", '[[rule]]\nid = "custom.scratch"\npaths = ["/scratch/"]\n'
    )
    _, out, _ = repo.run("rules", "-p", "custom", "--json", str(repo.root))
    [rule] = json.loads(out)["rules"]
    assert rule["id"] == "custom.scratch" and rule["risk"] == "custom"
    assert rule["default"] is True
    _, out, _ = repo.run("profiles", "--json", str(repo.root))
    custom = next(p for p in json.loads(out)["profiles"] if p["id"] == "custom")
    assert custom["custom"] == 1 and custom["rules"] == 1
