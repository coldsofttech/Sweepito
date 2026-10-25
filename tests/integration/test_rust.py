"""Integration tests for the rust profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="rust",
    profile="rust",
    markers={"Cargo.toml": "[package]\nname='x'\n"},
    targets={
        "rust.profiling": ["flamegraph.svg", "perf.data", "perf.data.old"],
        "rust.target": ["target/"],
    },
    blocked_without={},
)

CASES = [CASE]


class TestRust(ProfileSuite):
    case = CASE
