"""Integration tests for the cornea profile."""

from tests.integration.profiles.support import Case, ProfileSuite

CASE = Case(
    id="cornea",
    profile="cornea",
    markers={"cornea.toml": ""},
    targets={
        "cornea.log": ["cornea.log", "cornea.log.1", "cornea.log.3"],
    },
    blocked_without={"cornea.log": ["cornea.toml"]},
)

CASES = [CASE]


class TestCornea(ProfileSuite):
    case = CASE
