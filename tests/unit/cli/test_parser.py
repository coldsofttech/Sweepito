from __future__ import annotations

from collections.abc import Callable

import pytest

from sweepito import __version__
from sweepito.cli import commands
from sweepito.cli.parser import RISK_CHOICES, build_parser


@pytest.mark.parametrize(
    ("argv", "handler"),
    [
        (["scan"], commands.cmd_scan),
        (["clean"], commands.cmd_clean),
        (["check"], commands.cmd_check),
        (["report"], commands.cmd_report),
        (["rules"], commands.cmd_rules),
        (["profiles"], commands.cmd_profiles),
        (["config", "show"], commands.cmd_config),
        (["config", "validate"], commands.cmd_config),
        (["init"], commands.cmd_init),
        (["hook", "install"], commands.cmd_hook),
        (["hook", "uninstall"], commands.cmd_hook),
        (["hook", "status"], commands.cmd_hook),
        (["doctor"], commands.cmd_doctor),
    ],
)
def test_each_command_dispatches_to_its_handler(
    argv: list[str], handler: Callable[..., int]
) -> None:
    assert build_parser().parse_args(argv).func is handler


def test_no_command_leaves_func_unset() -> None:
    assert getattr(build_parser().parse_args([]), "func", None) is None


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"sweepito {__version__}"


def test_global_options_have_sensible_defaults() -> None:
    args = build_parser().parse_args(["scan"])
    assert args.config is None and args.path is None
    assert not (args.json or args.quiet or args.verbose or args.no_color or args.hook)


def test_global_options_are_parsed() -> None:
    args = build_parser().parse_args(
        ["scan", "--json", "-q", "-v", "--no-color", "--config", "c.toml", "proj"]
    )
    assert args.json and args.quiet and args.verbose and args.no_color
    assert args.config == "c.toml" and args.path == "proj"


def test_selection_options_are_repeatable() -> None:
    args = build_parser().parse_args(
        ["scan", "-p", "python", "-p", "node", "--enable", "a.b", "--enable", "c.d"]
        + ["--disable", "e.f", "-x", "dist/", "-x", "out/", "--no-git-check"]
    )
    assert args.profiles == ["python", "node"]
    assert args.enable == ["a.b", "c.d"] and args.disable == ["e.f"]
    assert args.exclude == ["dist/", "out/"]
    assert args.no_git_check is True


@pytest.mark.parametrize("command", ["scan", "clean", "check", "report", "rules"])
def test_risk_choices_are_validated(command: str) -> None:
    parser = build_parser()
    for risk in RISK_CHOICES:
        assert parser.parse_args([command, "--risk", risk]).risk == risk
    with pytest.raises(SystemExit) as exc:
        parser.parse_args([command, "--risk", "bogus"])
    assert exc.value.code == 2


def test_clean_flags() -> None:
    args = build_parser().parse_args(["clean", "-n", "-y", "--non-interactive"])
    assert args.dry_run and args.yes and args.non_interactive
    defaults = build_parser().parse_args(["clean"])
    assert not (defaults.dry_run or defaults.yes or defaults.non_interactive)


def test_rules_and_profiles_explain() -> None:
    assert build_parser().parse_args(["rules", "--explain", "a.b"]).explain == "a.b"
    assert build_parser().parse_args(["profiles", "--explain", "py"]).explain == "py"


def test_hook_stage_defaults_and_choices() -> None:
    parser = build_parser()
    assert parser.parse_args(["hook", "install"]).stage == "post-commit"
    chosen = parser.parse_args(["hook", "install", "--stage", "pre-commit"])
    assert chosen.stage == "pre-commit"
    with pytest.raises(SystemExit):
        parser.parse_args(["hook", "install", "--stage", "pre-push"])
    with pytest.raises(SystemExit):
        parser.parse_args(["hook", "status", "--stage", "pre-commit"])


@pytest.mark.parametrize("command", ["config", "hook"])
def test_group_commands_require_an_action(command: str) -> None:
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args([command])
    assert exc.value.code == 2


def test_init_force_flag() -> None:
    assert build_parser().parse_args(["init", "--force"]).force is True
    assert build_parser().parse_args(["init"]).force is False
