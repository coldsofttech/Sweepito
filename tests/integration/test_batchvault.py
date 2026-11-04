"""Integration tests for the batchvault profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="batchvault",
    profile="batchvault",
    markers={"batchvault.toml": "[log]\nlevel = 'INFO'\n"},
    targets={
        "batchvault.staging": [".batchvault-abc123/", "backups/.batchvault-x9y8/"],
    },
)

CASES = [CASE]


class TestBatchVault(ProfileSuite):
    case = CASE
