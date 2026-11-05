"""Integration tests for the data-eng profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="data-eng",
    profile="data-eng",
    markers={"dbt_project.yml": "name: x\n", "build.sbt": ""},
    targets={
        "dbt.logs": ["logs/"],
        "dbt.packages": ["dbt_packages/"],
        "dbt.target": ["target/"],
        "spark.warehouse": ["spark-warehouse/"],
    },
    blocked_without={
        "dbt.logs": ["dbt_project.yml"],
        "dbt.packages": ["dbt_project.yml"],
        "dbt.target": ["dbt_project.yml"],
        "spark.warehouse": ["build.sbt"],
    },
)

CASES = [CASE]


class TestDataEng(ProfileSuite):
    case = CASE
