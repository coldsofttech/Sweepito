"""Integration tests for the ruby profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="ruby",
    profile="ruby",
    markers={"Gemfile": "", "config/application.rb": ""},
    targets={
        "rails.logs": ["log/development.log"],
        "rails.tmp": ["tmp/pids/", "tmp/sockets/"],
        "rails.tmp-cache": ["tmp/cache/"],
        "ruby.coverage": ["coverage/"],
        "ruby.vendor-bundle": ["vendor/bundle/"],
        "ruby.yard": [".yardoc/"],
    },
    blocked_without={
        "rails.logs": ["config/application.rb"],
        "rails.tmp": ["config/application.rb"],
        "rails.tmp-cache": ["config/application.rb"],
        "ruby.coverage": ["Gemfile"],
        "ruby.vendor-bundle": ["Gemfile"],
        "ruby.yard": ["Gemfile"],
    },
)

CASES = [CASE]


class TestRuby(ProfileSuite):
    case = CASE
