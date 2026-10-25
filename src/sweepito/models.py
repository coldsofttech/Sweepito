"""Data types shared by the API and the command line."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

from sweepito.errors import ConfigError


class Risk(IntEnum):
    CUSTOM = -1  # user-defined rules: ordered below safe, so any ceiling includes them
    SAFE = 0
    CONFIGURABLE = 1
    HIGH_IMPACT = 2

    @property
    def label(self) -> str:
        return self.name.lower().replace("_", "-")

    @classmethod
    def parse(cls, value: object) -> Risk:
        if isinstance(value, str):
            key = value.strip().upper().replace("-", "_")
            if key in cls.__members__:
                return cls[key]
        raise ConfigError(
            f"Invalid risk level {value!r}; expected custom, safe, configurable "
            "or high-impact."
        )


@dataclass(frozen=True)
class Rule:
    id: str
    profile: str
    paths: tuple[str, ...]
    risk: Risk
    requires: tuple[str, ...] = ()
    description: str = ""
    allow_untracked: bool = False
    builtin: bool = True


@dataclass(frozen=True)
class Profile:
    id: str
    description: str
    markers: tuple[str, ...]
    rules: tuple[Rule, ...]

    @property
    def always(self) -> bool:
        """A profile without markers is always active."""
        return not self.markers

    def risk_counts(self) -> dict[str, int]:
        counts = {"safe": 0, "configurable": 0, "high-impact": 0, "custom": 0}
        for rule in self.rules:
            counts[rule.risk.label] += 1
        return counts


@dataclass(frozen=True)
class Candidate:
    rule: str
    profile: str
    risk: Risk
    path: str  # posix, relative to the project root, no trailing slash
    is_dir: bool
    size: int

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "profile": self.profile,
            "risk": self.risk.label,
            "path": self.path,
            "is_dir": self.is_dir,
            "size": self.size,
        }


@dataclass(frozen=True)
class Skipped:
    path: str
    rule: str
    reason: str

    def to_dict(self) -> dict:
        return {"path": self.path, "rule": self.rule, "reason": self.reason}


@dataclass
class Plan:
    root: Path
    profiles: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)

    @property
    def total_bytes(self) -> int:
        return sum(c.size for c in self.candidates)

    def to_dict(self) -> dict:
        return {
            "root": str(self.root),
            "profiles": self.profiles,
            "candidates": [c.to_dict() for c in self.candidates],
            "skipped": [s.to_dict() for s in self.skipped],
            "total_bytes": self.total_bytes,
        }


@dataclass(frozen=True)
class Failure:
    path: str
    error: str

    def to_dict(self) -> dict:
        return {"path": self.path, "error": self.error}


@dataclass
class CleanResult:
    removed: list[Candidate] = field(default_factory=list)
    failed: list[Failure] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)
    freed_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "removed": [c.to_dict() for c in self.removed],
            "failed": [f.to_dict() for f in self.failed],
            "skipped": [s.to_dict() for s in self.skipped],
            "freed_bytes": self.freed_bytes,
        }


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"
