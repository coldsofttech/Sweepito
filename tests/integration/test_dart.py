"""Integration tests for the dart profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="dart",
    profile="dart",
    markers={"pubspec.yaml": "name: x\n"},
    targets={
        "dart.build": ["build/"],
        "dart.legacy": [
            ".packages",
            ".flutter-plugins",
            ".flutter-plugins-dependencies",
        ],
        "dart.tool": [".dart_tool/"],
    },
    blocked_without={},
)

CASES = [CASE]


class TestDart(ProfileSuite):
    case = CASE
