"""Integration tests for the clojure profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="clojure",
    profile="clojure",
    markers={"project.clj": "", "deps.edn": ""},
    targets={"clojure.cpcache": [".cpcache/"], "clojure.target": ["target/"]},
    blocked_without={
        "clojure.cpcache": ["deps.edn"],
        "clojure.target": ["project.clj", "deps.edn"],
    },
)

CASES = [CASE]


class TestClojure(ProfileSuite):
    case = CASE
