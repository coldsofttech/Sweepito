"""Shared harness for the per-profile integration tests.

Each ``test_<profile>.py`` defines a :class:`Case` (marker files a project of that
technology would contain, plus the git-ignored paths each rule should clean) and a
suite class inheriting :class:`ProfileSuite`. A target ending in ``/`` is created as a
directory holding one file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path

import pytest

from sweepito.models import Risk
from sweepito.registry import Registry
from tests.conftest import Repo

ALL_RISKS = ("--risk", "high-impact")
REGISTRY = Registry.build()


@dataclass(frozen=True)
class Case:
    id: str
    profile: str
    markers: dict[str, str]
    targets: dict[str, list[str]]
    # rule id -> marker files that rule needs; withholding them must block the rule
    blocked_without: dict[str, list[str]] = field(default_factory=dict)


def expected(case: Case, *, safe_only: bool = False) -> dict[str, str]:
    out: dict[str, str] = {}
    for rule_id, paths in case.targets.items():
        if safe_only and REGISTRY.rules[rule_id].risk is not Risk.SAFE:
            continue
        for path in paths:
            out[path.rstrip("/")] = rule_id
    return out


def build(repo: Repo, case: Case, markers: dict[str, str] | None = None) -> None:
    """Create marker files, targets, and a .gitignore that ignores only the targets."""
    markers = case.markers if markers is None else markers
    for name, content in markers.items():
        repo.write(name, content)
    ignores = []
    for paths in case.targets.values():
        for path in paths:
            ignores.append("/" + path.rstrip("/"))
            repo.write(path + "placeholder.bin" if path.endswith("/") else path, "data")
    repo.write(".gitignore", "\n".join(ignores) + "\n")


def satisfies(marker_path: str, requirement: str) -> bool:
    segments = requirement.count("/") + 1
    tail = "/".join(marker_path.split("/")[-segments:])
    return fnmatchcase(tail, requirement)


def fresh_repo(base: Path, name: str, capsys: pytest.CaptureFixture[str]) -> Repo:
    root = base / name
    root.mkdir()
    repo = Repo(root, capsys)
    repo.git("init", "-q")
    return repo


class ProfileSuite:
    """Standard checks for one :class:`Case`; set ``case`` on the subclass."""

    case: Case

    def test_every_rule_matches_exactly_its_targets(self, repo: Repo) -> None:
        build(repo, self.case)
        found = repo.candidates(*ALL_RISKS, "-p", self.case.profile)
        assert found == expected(self.case)

    def test_auto_detection_with_defaults_selects_only_safe_rules(
        self, repo: Repo
    ) -> None:
        build(repo, self.case)
        assert repo.candidates() == expected(self.case, safe_only=True)

    def test_clean_removes_targets_and_keeps_markers(self, repo: Repo) -> None:
        build(repo, self.case)
        code, data = repo.json("clean", "--yes", *ALL_RISKS, "-p", self.case.profile)
        assert code == 0 and data["failed"] == []
        for path in expected(self.case):
            assert not repo.exists(path), path
        for marker in self.case.markers:
            assert repo.exists(marker), marker
        assert repo.exists(".gitignore")

    def test_nothing_matches_without_marker_files(self, repo: Repo) -> None:
        if not self.case.markers:
            pytest.skip("profile has no markers; it is always active")
        build(repo, self.case, markers={})
        assert repo.candidates(*ALL_RISKS, "-p", self.case.profile) == {}
        # Auto-detection must not activate the profile; only always-on common rules.
        auto = repo.candidates("--risk", "configurable")
        assert all(rule.startswith("common.") for rule in auto.values()), auto

    def test_each_rule_is_blocked_without_its_own_marker(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        if not self.case.blocked_without:
            pytest.skip("no rule in this profile declares its own requires")
        for rule_id, withheld in self.case.blocked_without.items():
            remaining = {
                name: content
                for name, content in self.case.markers.items()
                if name not in withheld
            }
            repo = fresh_repo(tmp_path, rule_id, capsys)
            build(repo, self.case, markers=remaining)
            found = repo.candidates(*ALL_RISKS, "-p", self.case.profile)
            assert rule_id not in found.values(), f"{rule_id} fired without its marker"
