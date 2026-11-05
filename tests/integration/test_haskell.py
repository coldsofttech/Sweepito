"""Integration tests for the haskell profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="haskell",
    profile="haskell",
    markers={"app.cabal": "", "stack.yaml": ""},
    targets={
        "haskell.dist-newstyle": ["dist-newstyle/"],
        "haskell.stack-work": [".stack-work/"],
    },
    blocked_without={
        "haskell.dist-newstyle": ["app.cabal"],
        "haskell.stack-work": ["stack.yaml"],
    },
)

CASES = [CASE]


class TestHaskell(ProfileSuite):
    case = CASE
