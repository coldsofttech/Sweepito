"""Integration tests for the unity profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="unity",
    profile="unity",
    markers={"ProjectSettings/ProjectVersion.txt": ""},
    targets={
        "unity.temp": ["Temp/"],
        "unity.obj": ["obj/"],
        "unity.library": ["Library/"],
    },
    blocked_without={
        "unity.temp": ["ProjectSettings/ProjectVersion.txt"],
        "unity.obj": ["ProjectSettings/ProjectVersion.txt"],
        "unity.library": ["ProjectSettings/ProjectVersion.txt"],
    },
)

CASES = [CASE]


class TestUnity(ProfileSuite):
    case = CASE
