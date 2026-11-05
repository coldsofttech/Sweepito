"""Integration tests for the scala profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="scala",
    profile="scala",
    markers={"build.sbt": ""},
    targets={"scala.target": ["target/", "project/target/"]},
    blocked_without={"scala.target": ["build.sbt"]},
)

CASES = [CASE]


class TestScala(ProfileSuite):
    case = CASE
