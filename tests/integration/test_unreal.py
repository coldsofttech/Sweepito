"""Integration tests for the unreal profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="unreal",
    profile="unreal",
    markers={"Game.uproject": ""},
    targets={
        "unreal.intermediate": ["Intermediate/"],
        "unreal.binaries": ["Binaries/"],
    },
    blocked_without={
        "unreal.intermediate": ["Game.uproject"],
        "unreal.binaries": ["Game.uproject"],
    },
)

CASES = [CASE]


class TestUnreal(ProfileSuite):
    case = CASE
