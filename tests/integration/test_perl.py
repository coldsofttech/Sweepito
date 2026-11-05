"""Integration tests for the perl profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="perl",
    profile="perl",
    markers={"Makefile.PL": "", "Build.PL": ""},
    targets={
        "perl.blib": ["blib/", "pm_to_blib"],
        "perl.build-dir": ["_build/"],
        "perl.mymeta": ["MYMETA.json", "MYMETA.yml"],
    },
    blocked_without={
        "perl.blib": ["Makefile.PL", "Build.PL"],
        "perl.build-dir": ["Build.PL"],
        "perl.mymeta": ["Makefile.PL", "Build.PL"],
    },
)

CASES = [CASE]


class TestPerl(ProfileSuite):
    case = CASE
