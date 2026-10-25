"""Integration tests for the node-pm profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="node-pm",
    profile="node-pm",
    markers={"package.json": "{}", "pnpm-lock.yaml": "", "yarn.lock": ""},
    targets={
        "node-pm.pnpm-store": [".pnpm-store/"],
        "node-pm.yarn-cache": [".yarn/cache/"],
    },
    blocked_without={
        "node-pm.pnpm-store": ["pnpm-lock.yaml"],
        "node-pm.yarn-cache": ["yarn.lock"],
    },
)

CASES = [CASE]


class TestNodePm(ProfileSuite):
    case = CASE
