"""Integration tests for the godot profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="godot",
    profile="godot",
    markers={"project.godot": ""},
    targets={"godot.cache": [".godot/"]},
    blocked_without={"godot.cache": ["project.godot"]},
)

CASES = [CASE]


class TestGodot(ProfileSuite):
    case = CASE
