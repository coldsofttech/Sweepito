from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from sweepito.cli import main


class Repo:
    def __init__(self, root: Path, capsys: pytest.CaptureFixture[str]) -> None:
        self.root = root
        self._capsys = capsys

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), *args], check=True, capture_output=True
        )

    def write(self, rel: str, content: str = "x") -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def exists(self, rel: str) -> bool:
        return (self.root / rel).exists() or (self.root / rel).is_symlink()

    def run(self, *args: str) -> tuple[int, str, str]:
        self._capsys.readouterr()
        code = main([*args, "--no-color"])
        captured = self._capsys.readouterr()
        return code, captured.out, captured.err

    def json(self, *args: str) -> tuple[int, dict]:
        code, out, _ = self.run(*args, "--json", str(self.root))
        return code, (json.loads(out) if out.strip() else {})

    def candidates(self, *args: str) -> dict[str, str]:
        code, data = self.json("scan", *args)
        assert code == 0, data
        return {c["path"]: c["rule"] for c in data["candidates"]}


@pytest.fixture
def repo(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Repo:
    root = tmp_path / "proj"
    root.mkdir()
    project = Repo(root, capsys)
    project.git("init", "-q")
    return project
