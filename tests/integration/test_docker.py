"""Integration tests for the docker profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="docker",
    profile="docker",
    markers={"Dockerfile": "FROM scratch\n"},
    targets={
        "docker.buildx-cache": [".buildx-cache/", ".buildx-cache-new/"],
    },
    blocked_without={
        "docker.buildx-cache": ["Dockerfile"],
    },
)

CASES = [CASE]


class TestDocker(ProfileSuite):
    case = CASE
