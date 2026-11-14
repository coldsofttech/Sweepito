"""Integration tests for the commitrocket profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="commitrocket",
    profile="commitrocket",
    markers={"commitrocket.toml": "", ".commitrocketignore": ""},
    targets={
        "commitrocket.report-tmp": [
            "out.json.k3j2x9.tmp",
            "sub/report.json.a1b2c3.tmp",
        ],
    },
    blocked_without={},
)

CASES = [CASE]


class TestCommitRocket(ProfileSuite):
    case = CASE
