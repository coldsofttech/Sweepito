"""Integration tests for the terraform profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="terraform",
    profile="terraform",
    markers={"main.tf": "", "terragrunt.hcl": ""},
    targets={
        "terraform.crash-log": ["crash.log"],
        "terraform.dir": [".terraform/"],
        "terraform.plans": ["plan.tfplan"],
        "terragrunt.cache": [".terragrunt-cache/"],
    },
    blocked_without={
        "terraform.crash-log": ["main.tf"],
        "terraform.dir": ["main.tf"],
        "terraform.plans": ["main.tf"],
        "terragrunt.cache": ["terragrunt.hcl"],
    },
)

CASES = [CASE]


class TestTerraform(ProfileSuite):
    case = CASE
