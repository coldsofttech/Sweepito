from __future__ import annotations

from pathlib import Path

import pytest

from sweepito import api
from sweepito.config import Options
from sweepito.errors import ConfigError
from sweepito.models import Risk

CUSTOM_RULE = '[[rule]]\nid = "custom.out"\npaths = ["out/"]\n'


def make_project(root: Path) -> Path:
    root.mkdir(exist_ok=True)
    (root / "sweepito.toml").write_text(CUSTOM_RULE, encoding="utf-8")
    (root / "out").mkdir()
    (root / "out" / "artifact.bin").write_text("x" * 100, encoding="utf-8")
    (root / "keep.txt").write_text("source", encoding="utf-8")
    return root


def test_resolve_root_returns_the_given_directory(tmp_path: Path) -> None:
    assert api.resolve_root(str(tmp_path)) == tmp_path.resolve()


def test_resolve_root_rejects_a_path_that_is_not_a_directory(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(ConfigError, match="Not a directory"):
        api.resolve_root(str(missing))


def test_resolve_root_falls_back_to_the_cwd_outside_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert api.resolve_root() == tmp_path.resolve()


def test_prepare_uses_defaults_without_a_config_file(tmp_path: Path) -> None:
    ctx = api.prepare(tmp_path)
    assert ctx.root == tmp_path
    assert ctx.config.path is None
    assert ctx.settings.risk is Risk.SAFE
    assert ctx.settings.profiles == ("auto",)
    assert ctx.in_git is False


def test_prepare_rejects_a_missing_config_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Config file not found"):
        api.prepare(tmp_path, config_file=str(tmp_path / "nope.toml"))


def test_prepare_applies_an_explicit_config_file(tmp_path: Path) -> None:
    config = tmp_path / "custom.toml"
    config.write_text('[defaults]\nrisk = "configurable"\n', encoding="utf-8")
    ctx = api.prepare(tmp_path, config_file=str(config))
    assert ctx.config.path == config
    assert ctx.settings.risk is Risk.CONFIGURABLE


def test_prepare_options_beat_the_config_file(tmp_path: Path) -> None:
    (tmp_path / "sweepito.toml").write_text(
        '[defaults]\nrisk = "configurable"\n', encoding="utf-8"
    )
    ctx = api.prepare(tmp_path, Options(risk=Risk.SAFE))
    assert ctx.settings.risk is Risk.SAFE


def test_prepare_discovers_config_and_registers_custom_rules(tmp_path: Path) -> None:
    ctx = api.prepare(make_project(tmp_path / "proj"))
    assert ctx.config.path is not None
    assert "custom.out" in ctx.registry.rules


def test_scan_lists_candidates_without_deleting(tmp_path: Path) -> None:
    root = make_project(tmp_path / "proj")
    ctx = api.prepare(root, Options(no_git_check=True))
    plan = api.scan(ctx)
    assert [c.path for c in plan.candidates] == ["out"]
    assert (root / "out" / "artifact.bin").exists()


def test_clean_removes_planned_candidates_only(tmp_path: Path) -> None:
    root = make_project(tmp_path / "proj")
    ctx = api.prepare(root, Options(no_git_check=True))
    result = api.clean(ctx, api.scan(ctx))
    assert [c.path for c in result.removed] == ["out"]
    assert not result.failed
    assert result.freed_bytes >= 100
    assert not (root / "out").exists()
    assert (root / "keep.txt").exists()
