"""Integration tests for the elixir profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="elixir",
    profile="elixir",
    markers={"mix.exs": ""},
    targets={
        "elixir.build": ["_build/"],
        "elixir.cover": ["cover/"],
        "elixir.crash": ["erl_crash.dump"],
        "elixir.deps": ["deps/"],
        "elixir.ls": [".elixir_ls/"],
        "phoenix.static": ["priv/static/"],
    },
    blocked_without={},
)

CASES = [CASE]


class TestElixir(ProfileSuite):
    case = CASE
