"""Configuration discovery, validation and merging with command line options."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from sweepito.errors import ConfigError
from sweepito.models import Risk, Rule
from sweepito.registry import CUSTOM_PROFILE

CONFIG_NAMES = ("sweepito.toml", ".sweepito.toml")

_DEFAULTS_KEYS = {"profiles", "risk"}
_CLEAN_KEYS = {"enable", "disable", "exclude"}
_HOOK_KEYS = {"risk", "quiet"}
_RULE_KEYS = {
    "id",
    "paths",
    "requires",
    "risk",
    "profile",
    "description",
    "allow_untracked",
    "exec",
}
_PROFILE_KEYS = {"markers", "description"}
_TOP_KEYS = {"defaults", "clean", "hook", "rule", "profile"}
_RULE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


@dataclass
class FileConfig:
    """Validated contents of a configuration file."""

    path: Path | None = None
    profiles: tuple[str, ...] | None = None
    risk: Risk | None = None
    enable: tuple[str, ...] = ()
    disable: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    hook_risk: Risk | None = None
    hook_quiet: bool = False
    rules: tuple[Rule, ...] = ()
    profile_defs: dict[str, tuple[tuple[str, ...], str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Options:
    """Command line choices. ``None`` or empty means "not given"."""

    profiles: tuple[str, ...] = ()
    enable: tuple[str, ...] = ()
    disable: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    risk: Risk | None = None
    no_git_check: bool = False
    hook: bool = False


@dataclass(frozen=True)
class Settings:
    """Effective settings after merging command line, file and defaults."""

    profiles: tuple[str, ...] = ("auto",)
    risk: Risk = Risk.SAFE
    enable: tuple[str, ...] = ()
    disable: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    no_git_check: bool = False
    quiet: bool = False

    def to_dict(self) -> dict:
        return {
            "profiles": list(self.profiles),
            "risk": self.risk.label,
            "enable": list(self.enable),
            "disable": list(self.disable),
            "exclude": list(self.exclude),
            "no_git_check": self.no_git_check,
            "quiet": self.quiet,
        }


def find_config(start: Path, stop: Path | None = None) -> Path | None:
    """Search ``start`` and its parents (up to ``stop``) for a config file."""
    current = start.resolve()
    stop = stop.resolve() if stop else None
    while True:
        for name in CONFIG_NAMES:
            candidate = current / name
            if candidate.is_file():
                return candidate
        pyproject = current / "pyproject.toml"
        if pyproject.is_file() and _has_pyproject_table(pyproject):
            return pyproject
        if current == stop or current.parent == current:
            return None
        current = current.parent


def _read_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc


def _has_pyproject_table(path: Path) -> bool:
    try:
        return "sweepito" in _read_toml(path).get("tool", {})
    except ConfigError:
        return False


def _norm(table: dict) -> dict:
    return {key.replace("-", "_"): value for key, value in table.items()}


def _table(value: object, where: str, allowed: set[str]) -> dict:
    if not isinstance(value, dict):
        raise ConfigError(f"[{where}] must be a table.")
    table = _norm(value)
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise ConfigError(f"Unknown key(s) in [{where}]: {', '.join(unknown)}.")
    return table


def _strings(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ConfigError(f"{where} must be a list of strings.")
    return tuple(value)


def validate_pattern(pattern: str, where: str) -> None:
    """Reject patterns that could escape the project root or negate matches."""
    problems = (
        not pattern.strip(),
        pattern.startswith(("!", "#", "~")),
        "\\" in pattern,
        bool(re.match(r"^[A-Za-z]:", pattern)),
        pattern.startswith("//"),
        ".." in pattern.split("/"),
    )
    if any(problems):
        raise ConfigError(f"Unsafe or invalid path pattern {pattern!r} in {where}.")


def _parse_rule(raw: object, index: int) -> Rule:
    where = f"[[rule]] #{index + 1}"
    table = _table(raw, where, _RULE_KEYS)
    if "exec" in table:
        raise ConfigError(
            f"{where}: command rules ('exec') are not supported yet. "
            "Use 'paths' for declarative cleanup."
        )
    if "risk" in table:
        raise ConfigError(
            f"{where}: custom rules do not take a 'risk' level; they always run. "
            "Use 'disable' to switch one off."
        )
    rule_id = table.get("id")
    if not isinstance(rule_id, str) or not _RULE_ID.match(rule_id):
        raise ConfigError(
            f"{where}: 'id' is required (lowercase letters, digits, . _ -)."
        )
    paths = _strings(table.get("paths"), f"{where} 'paths'")
    if not paths:
        raise ConfigError(f"{where}: 'paths' must not be empty.")
    for pattern in paths:
        validate_pattern(pattern, f"rule {rule_id!r}")
    requires = _strings(table.get("requires", []), f"{where} 'requires'")
    allow_untracked = table.get("allow_untracked", False)
    if not isinstance(allow_untracked, bool):
        raise ConfigError(f"{where}: 'allow_untracked' must be true or false.")
    profile = table.get("profile", CUSTOM_PROFILE)
    if not isinstance(profile, str) or not profile:
        raise ConfigError(f"{where}: 'profile' must be a non-empty string.")
    return Rule(
        id=rule_id,
        profile=profile,
        paths=paths,
        risk=Risk.CUSTOM,
        requires=requires,
        description=str(table.get("description", "")),
        allow_untracked=allow_untracked,
        builtin=False,
    )


def load_config(path: Path) -> FileConfig:
    data = _read_toml(path)
    if path.name == "pyproject.toml":
        data = data.get("tool", {}).get("sweepito", {})
    unknown = sorted(set(map(str, data)) - _TOP_KEYS)
    if unknown:
        raise ConfigError(f"Unknown section(s) in {path.name}: {', '.join(unknown)}.")

    cfg = FileConfig(path=path)
    if "defaults" in data:
        table = _table(data["defaults"], "defaults", _DEFAULTS_KEYS)
        if "profiles" in table:
            cfg.profiles = _strings(table["profiles"], "[defaults] profiles")
        if "risk" in table:
            cfg.risk = Risk.parse(table["risk"])
    if "clean" in data:
        table = _table(data["clean"], "clean", _CLEAN_KEYS)
        cfg.enable = _strings(table.get("enable", []), "[clean] enable")
        cfg.disable = _strings(table.get("disable", []), "[clean] disable")
        cfg.exclude = _strings(table.get("exclude", []), "[clean] exclude")
    if "hook" in data:
        table = _table(data["hook"], "hook", _HOOK_KEYS)
        if "risk" in table:
            cfg.hook_risk = Risk.parse(table["risk"])
        quiet = table.get("quiet", False)
        if not isinstance(quiet, bool):
            raise ConfigError("[hook] quiet must be true or false.")
        cfg.hook_quiet = quiet
    if "rule" in data:
        raw_rules = data["rule"]
        if not isinstance(raw_rules, list):
            raise ConfigError("'rule' must be an array of tables ([[rule]]).")
        rules = tuple(_parse_rule(raw, i) for i, raw in enumerate(raw_rules))
        ids = [r.id for r in rules]
        if len(ids) != len(set(ids)):
            raise ConfigError("Duplicate rule IDs in [[rule]] entries.")
        cfg.rules = rules
    if "profile" in data:
        profiles = data["profile"]
        if not isinstance(profiles, dict):
            raise ConfigError(
                "[profile] must contain named tables, e.g. [profile.myteam]."
            )
        for name, raw in profiles.items():
            table = _table(raw, f"profile.{name}", _PROFILE_KEYS)
            cfg.profile_defs[name] = (
                _strings(table.get("markers", []), f"[profile.{name}] markers"),
                str(table.get("description", "")),
            )
    return cfg


def merge(options: Options, cfg: FileConfig) -> Settings:
    """CLI beats file beats defaults; list options are combined."""
    risk = options.risk
    if risk is None and options.hook:
        risk = cfg.hook_risk
    if risk is None:
        risk = cfg.risk
    if risk is None:
        risk = Risk.SAFE
    profiles = options.profiles or cfg.profiles or ("auto",)
    for pattern in options.exclude + cfg.exclude:
        validate_pattern(pattern, "exclude")
    return Settings(
        profiles=tuple(profiles),
        risk=risk,
        enable=cfg.enable + options.enable,
        disable=cfg.disable + options.disable,
        exclude=cfg.exclude + options.exclude,
        no_git_check=options.no_git_check,
        quiet=options.hook and cfg.hook_quiet,
    )
