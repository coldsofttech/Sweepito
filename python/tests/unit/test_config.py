from __future__ import annotations

import pathspec
import pytest

from sweepito.config import Options, load_config, merge, validate_pattern
from sweepito.errors import ConfigError
from sweepito.models import Risk
from sweepito.registry import Registry


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
