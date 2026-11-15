"""Shared harness for the per-profile integration tests.

Each ``test_<profile>.py`` defines a :class:`Case` (marker files a project of that
technology would contain, plus the git-ignored paths each rule should clean) and a
suite class inheriting :class:`ProfileSuite`. A target ending in ``/`` is created as a
directory holding one file.
"""

from __future__ import annotations

import os
import shutil
import subprocess
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


def first_target(case: Case) -> str:
    """One path (no trailing slash) that the case expects to be cleaned."""
    return next(iter(expected(case)))


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

    def test_tracked_files_are_never_removed(self, repo: Repo) -> None:
        build(repo, self.case)
        target = first_target(self.case)
        tracked = next(
            t
            for paths in self.case.targets.values()
            for t in paths
            if t.rstrip("/") == target
        )
        is_dir = tracked.endswith("/")
        repo.git("add", "-f", tracked + "placeholder.bin" if is_dir else tracked)
        found = repo.candidates(*ALL_RISKS, "-p", self.case.profile)
        assert target not in found
        assert set(found) == set(expected(self.case)) - {target}
        code, data = repo.json("clean", "--yes", *ALL_RISKS, "-p", self.case.profile)
        assert code == 0 and data["failed"] == []
        assert repo.exists(target)

    def test_link_target_contents_are_never_removed(self, repo: Repo) -> None:
        build(repo, self.case)
        target = first_target(self.case)
        outside = repo.root.parent / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep", encoding="utf-8")
        path = repo.root / target
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        try:
            path.symlink_to(outside, target_is_directory=True)
        except OSError:
            # Windows without symlink rights: a junction needs no privileges.
            junction = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(path), str(outside)],
                capture_output=True,
                check=False,
            )
            if os.name != "nt" or junction.returncode != 0:
                pytest.skip("symbolic links are not available here")
        # The link itself may be removed, but never the folder it points at.
        code, data = repo.json("clean", "--yes", *ALL_RISKS, "-p", self.case.profile)
        assert code == 0 and data["failed"] == []
        assert (outside / "keep.txt").read_text(encoding="utf-8") == "keep"

    def test_nested_project_in_a_monorepo(self, repo: Repo) -> None:
        if not self.case.markers:
            pytest.skip("profile has no markers; it is always active")
        ignores = []
        for folder, with_markers in (("pkg", True), ("other", False)):
            if with_markers:
                for name, content in self.case.markers.items():
                    repo.write(f"{folder}/{name}", content)
            for paths in self.case.targets.values():
                for path in paths:
                    ignores.append(f"/{folder}/{path.rstrip('/')}")
                    repo.write(
                        f"{folder}/{path}"
                        + ("placeholder.bin" if path.endswith("/") else ""),
                        "data",
                    )
        repo.write(".gitignore", "\n".join(ignores) + "\n")
        found = repo.candidates(*ALL_RISKS, "-p", self.case.profile)
        assert found == {f"pkg/{p}": r for p, r in expected(self.case).items()}

    def test_exclude_protects_a_matching_target(self, repo: Repo) -> None:
        build(repo, self.case)
        target = first_target(self.case)
        repo.write("sweepito.toml", f'[clean]\nexclude = ["/{target}"]\n')
        found = repo.candidates(*ALL_RISKS, "-p", self.case.profile)
        assert found == {p: r for p, r in expected(self.case).items() if p != target}
        repo.json("clean", "--yes", *ALL_RISKS, "-p", self.case.profile)
        assert repo.exists(target)
