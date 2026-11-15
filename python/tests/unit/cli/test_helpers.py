from __future__ import annotations

import argparse
import builtins
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from sweepito.cli import helpers
from sweepito.errors import SafetyRefusal
from sweepito.models import Risk


def namespace(**values: object) -> argparse.Namespace:
    return argparse.Namespace(**{"hook": False, **values})


def test_build_options_reads_every_field() -> None:
    args = namespace(
        profiles=["python"],
        enable=["a.b"],
        disable=["c.d"],
        exclude=["dist/"],
        risk="configurable",
        no_git_check=True,
        hook=True,
    )
    options = helpers.build_options(args)
    assert options.profiles == ("python",)
    assert options.enable == ("a.b",)
    assert options.disable == ("c.d",)
    assert options.exclude == ("dist/",)
    assert options.risk is Risk.CONFIGURABLE
    assert options.no_git_check is True
    assert options.hook is True


def test_build_options_defaults_for_commands_without_those_flags() -> None:
    options = helpers.build_options(namespace())
    assert options.profiles == () and options.exclude == ()
    assert options.risk is None
    assert options.no_git_check is False


def test_emit_prints_indented_json(capsys: pytest.CaptureFixture[str]) -> None:
    helpers.emit({"a": 1})
    out = capsys.readouterr().out
    assert json.loads(out) == {"a": 1}
    assert out.startswith('{\n  "a"')


@pytest.mark.parametrize(
    ("flag", "setting", "expected"),
    [(True, False, True), (False, True, True), (False, False, False)],
)
def test_is_quiet_combines_the_flag_and_the_setting(
    flag: bool, setting: bool, expected: bool
) -> None:
    ctx = SimpleNamespace(settings=SimpleNamespace(quiet=setting))
    assert helpers.is_quiet(namespace(quiet=flag), ctx) is expected  # type: ignore[arg-type]


def test_empty_result_has_the_clean_result_keys() -> None:
    assert helpers.empty_result() == {"removed": [], "failed": [], "freed_bytes": 0}


def test_stderr_console_writes_to_stderr() -> None:
    assert helpers.stderr_console(namespace()).stderr is True
    assert helpers.stderr_console(namespace(no_color=True)).no_color is True


def test_get_context_resolves_the_root_and_config(tmp_path: Path) -> None:
    (tmp_path / "sweepito.toml").write_text(
        '[defaults]\nrisk = "configurable"\n', encoding="utf-8"
    )
    ctx = helpers.get_context(namespace(path=str(tmp_path), config=None))
    assert ctx.root == tmp_path.resolve()
    assert ctx.settings.risk is Risk.CONFIGURABLE


def test_get_plan_returns_the_context_and_its_plan(tmp_path: Path) -> None:
    (tmp_path / "sweepito.toml").write_text(
        '[[rule]]\nid = "custom.out"\npaths = ["out/"]\n', encoding="utf-8"
    )
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "a.bin").write_text("x", encoding="utf-8")
    args = namespace(path=str(tmp_path), config=None, no_git_check=True)
    ctx, plan = helpers.get_plan(args)
    assert ctx.root == plan.root
    assert [c.path for c in plan.candidates] == ["out"]


class FakeStdin:
    def __init__(self, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_confirm_is_false_without_a_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", FakeStdin(False))
    assert helpers.confirm(1, 10) is False


@pytest.mark.parametrize(
    ("answer", "expected"), [("y", True), (" YES ", True), ("n", False), ("", False)]
)
def test_confirm_reads_the_answer(
    monkeypatch: pytest.MonkeyPatch, answer: str, expected: bool
) -> None:
    monkeypatch.setattr(sys, "stdin", FakeStdin(True))
    monkeypatch.setattr(builtins, "input", lambda prompt: answer)
    assert helpers.confirm(2, 2048) is expected


def test_confirm_without_input_is_a_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_input(prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr(sys, "stdin", FakeStdin(True))
    monkeypatch.setattr(builtins, "input", no_input)
    with pytest.raises(SafetyRefusal, match="--yes"):
        helpers.confirm(1, 1)
