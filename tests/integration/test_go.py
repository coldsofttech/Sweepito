"""Integration tests for the go profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="go",
    profile="go",
    markers={"go.mod": "module x\n"},
    targets={
        "go.bin": ["bin/"],
        "go.coverage": ["coverage/"],
        "go.gocache": [".gocache/"],
        "go.test-artifacts": ["pkg.test", "cpu.prof", "coverage.out"],
        "go.vendor": ["vendor/"],
    },
    blocked_without={
        "go.coverage": ["go.mod"],
        "go.gocache": ["go.mod"],
    },
)

CASES = [CASE]


class TestGo(ProfileSuite):
    case = CASE
