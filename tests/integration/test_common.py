"""Integration tests for the common profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="common",
    profile="common",
    markers={},
    targets={
        "common.editor-temp": ["notes.txt.swp", "draft~"],
        "common.logs": ["app.log"],
        "common.merge-leftovers": ["a.orig", "b.rej"],
        "common.os-junk": [".DS_Store", "sub/Thumbs.db"],
        "common.pm-logs": ["npm-debug.log", "yarn-error.log"],
    },
    blocked_without={},
)

CASES = [CASE]


class TestCommon(ProfileSuite):
    case = CASE
