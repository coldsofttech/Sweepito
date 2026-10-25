"""Integration tests for the jvm profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="jvm",
    profile="jvm",
    markers={
        "app.iml": "",
        "build.gradle": "",
        "build.gradle.kts": "",
        "pom.xml": "<project/>",
        "settings.gradle": "",
    },
    targets={
        "jvm.gradle-build": ["build/"],
        "jvm.gradle-project": [".gradle/"],
        "jvm.idea-out": ["out/"],
        "jvm.kotlin": [".kotlin/"],
        "jvm.maven-target": ["target/"],
    },
    blocked_without={
        "jvm.gradle-build": ["build.gradle", "build.gradle.kts"],
        "jvm.gradle-project": ["build.gradle", "build.gradle.kts", "settings.gradle"],
        "jvm.idea-out": ["app.iml"],
        "jvm.kotlin": ["build.gradle", "build.gradle.kts"],
        "jvm.maven-target": ["pom.xml"],
    },
)

CASES = [CASE]


class TestJvm(ProfileSuite):
    case = CASE
