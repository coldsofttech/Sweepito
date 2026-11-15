from __future__ import annotations

import argparse
from collections.abc import Callable

import pytest

from sweepito import cli
from sweepito.cli import commands
from sweepito.errors import (
    EXIT_INTERRUPTED,
    EXIT_OK,
    EXIT_REFUSED,
    EXIT_UNEXPECTED,
    EXIT_USAGE,
    ConfigError,
    SafetyRefusal,
)


def raising(error: BaseException) -> Callable[[argparse.Namespace], int]:
    def handler(args: argparse.Namespace) -> int:
        raise error

    return handler


def test_package_exposes_main_and_build_parser() -> None:
    assert isinstance(cli.build_parser(), argparse.ArgumentParser)
    assert cli.build_parser().prog == "sweepito"
    assert callable(cli.main)


def test_no_command_prints_help_and_reports_a_usage_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main([]) == EXIT_USAGE
    assert "usage: sweepito" in capsys.readouterr().out


def test_returns_the_handler_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(commands, "cmd_scan", lambda args: 7)
    assert cli.main(["scan"]) == 7


def test_a_successful_handler_returns_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(commands, "cmd_scan", lambda args: EXIT_OK)
    assert cli.main(["scan"]) == EXIT_OK


def test_unknown_command_exits_through_argparse() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["nope"])
    assert exc.value.code == 2


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (ConfigError("bad config"), EXIT_USAGE),
        (SafetyRefusal("bad config"), EXIT_REFUSED),
    ],
)
def test_sweepito_errors_map_to_their_exit_code_on_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: Exception,
    code: int,
) -> None:
    monkeypatch.setattr(commands, "cmd_scan", raising(error))
    assert cli.main(["scan"]) == code
    captured = capsys.readouterr()
    assert "sweepito: error: bad config" in captured.err
    assert captured.out == ""


def test_keyboard_interrupt_is_reported(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(commands, "cmd_scan", raising(KeyboardInterrupt()))
    assert cli.main(["scan"]) == EXIT_INTERRUPTED
    assert "interrupted" in capsys.readouterr().err


def test_unexpected_errors_are_caught_last(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(commands, "cmd_scan", raising(RuntimeError("boom")))
    assert cli.main(["scan"]) == EXIT_UNEXPECTED
    assert "unexpected error: RuntimeError('boom')" in capsys.readouterr().err
