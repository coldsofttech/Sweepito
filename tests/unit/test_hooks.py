from __future__ import annotations

from pathlib import Path

import pytest

from sweepito import git, hooks
from sweepito.errors import ConfigError


@pytest.fixture
def hooks_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "hooks"
    monkeypatch.setattr(git, "hooks_dir", lambda root: directory)
    return directory


def test_hook_path_rejects_an_unknown_stage(tmp_path: Path, hooks_dir: Path) -> None:
    with pytest.raises(ConfigError, match="Unsupported hook stage"):
        hooks.hook_path(tmp_path, "pre-push")


def test_hook_path_is_inside_the_hooks_directory(
    tmp_path: Path, hooks_dir: Path
) -> None:
    assert hooks.hook_path(tmp_path, "pre-commit") == hooks_dir / "pre-commit"


def test_install_writes_a_shell_script_with_the_stage_command(
    tmp_path: Path, hooks_dir: Path
) -> None:
    path = hooks.install(tmp_path, "post-commit")
    text = path.read_text(encoding="utf-8")
    assert text.startswith("#!/bin/sh")
    assert hooks.BEGIN in text and hooks.END in text
    assert hooks.STAGES["post-commit"] in text
    assert "\r" not in text


def test_install_is_idempotent(tmp_path: Path, hooks_dir: Path) -> None:
    first = hooks.install(tmp_path, "pre-commit").read_text(encoding="utf-8")
    second = hooks.install(tmp_path, "pre-commit").read_text(encoding="utf-8")
    assert first == second
    assert second.count(hooks.BEGIN) == 1


def test_install_preserves_existing_hook_content(
    tmp_path: Path, hooks_dir: Path
) -> None:
    hooks_dir.mkdir()
    (hooks_dir / "post-commit").write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
    text = hooks.install(tmp_path).read_text(encoding="utf-8")
    assert "echo mine" in text
    assert hooks.STAGES["post-commit"] in text


def test_uninstall_removes_a_file_we_created(tmp_path: Path, hooks_dir: Path) -> None:
    path = hooks.install(tmp_path)
    assert hooks.uninstall(tmp_path) is True
    assert not path.exists()


def test_uninstall_keeps_content_we_did_not_write(
    tmp_path: Path, hooks_dir: Path
) -> None:
    hooks_dir.mkdir()
    (hooks_dir / "post-commit").write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
    hooks.install(tmp_path)
    assert hooks.uninstall(tmp_path) is True
    text = (hooks_dir / "post-commit").read_text(encoding="utf-8")
    assert "echo mine" in text
    assert hooks.BEGIN not in text


def test_uninstall_reports_when_nothing_is_installed(
    tmp_path: Path, hooks_dir: Path
) -> None:
    assert hooks.uninstall(tmp_path) is False
    hooks_dir.mkdir()
    (hooks_dir / "post-commit").write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
    assert hooks.uninstall(tmp_path) is False
    assert (hooks_dir / "post-commit").exists()


def test_status_reports_each_stage(tmp_path: Path, hooks_dir: Path) -> None:
    assert hooks.status(tmp_path) == {"post-commit": False, "pre-commit": False}
    hooks.install(tmp_path, "pre-commit")
    assert hooks.status(tmp_path) == {"post-commit": False, "pre-commit": True}
