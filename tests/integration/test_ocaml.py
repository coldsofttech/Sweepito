"""Integration tests for the ocaml profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="ocaml",
    profile="ocaml",
    markers={"dune-project": ""},
    targets={"ocaml.build": ["_build/"]},
    blocked_without={"ocaml.build": ["dune-project"]},
)

CASES = [CASE]


class TestOcaml(ProfileSuite):
    case = CASE
