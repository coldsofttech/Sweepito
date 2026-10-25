"""Integration tests for the r profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="r",
    profile="r",
    markers={
        "DESCRIPTION": "Package: x\n",
        "app.Rproj": "",
        "renv.lock": "{}",
        "report.Rmd": "",
    },
    targets={
        "r.history": [".Rhistory"],
        "r.knitr-cache": ["report_cache/", "report_files/"],
        "r.rcheck": ["pkg.Rcheck/"],
        "r.rdata": [".RData"],
        "r.renv-library": ["renv/library/"],
        "r.rproj-user": [".Rproj.user/"],
    },
    blocked_without={
        "r.knitr-cache": ["report.Rmd"],
        "r.renv-library": ["renv.lock"],
        "r.rproj-user": ["app.Rproj"],
    },
)

CASES = [CASE]


class TestR(ProfileSuite):
    case = CASE
