"""Integration tests for the dotnet profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="dotnet",
    profile="dotnet",
    markers={"App.csproj": "<Project/>", "App.sln": "", "Directory.Build.props": ""},
    targets={
        "dotnet.artifacts": ["artifacts/"],
        "dotnet.bin-obj": ["bin/", "obj/"],
        "dotnet.publish": ["publish/"],
        "dotnet.testresults": ["tests/TestResults/"],
        "dotnet.vs": [".vs/"],
    },
    blocked_without={
        "dotnet.artifacts": ["App.sln", "Directory.Build.props"],
        "dotnet.bin-obj": ["App.csproj"],
        "dotnet.publish": ["App.csproj"],
        "dotnet.vs": ["App.sln"],
    },
)

CASES = [CASE]


class TestDotnet(ProfileSuite):
    case = CASE
