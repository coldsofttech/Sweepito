"""Integration tests for the batchvault profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="batchvault",
    profile="batchvault",
    markers={"batchvault.toml": ""},
    targets={
        "batchvault.staging": [".batchvault-abc123/"],
        "batchvault.manifest-tmp": ["manifest.json.k3j2x9.tmp"],
    },
    blocked_without={
        "batchvault.staging": ["batchvault.toml"],
        "batchvault.manifest-tmp": ["batchvault.toml"],
    },
)

CASES = [CASE]


class TestBatchVault(ProfileSuite):
    case = CASE
