"""Integration tests for the jvm profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="jvm",
    profile="jvm",
    markers={
        "app.iml": "",
        "build.gradle": "",
        "build.gradle.kts": "",
        "build.sbt": "",
        "pom.xml": "<project/>",
        "settings.gradle": "",
    },
    targets={
        "jvm.gradle-build": ["build/"],
        "jvm.gradle-project": [".gradle/"],
        "jvm.idea-out": ["out/"],
        "jvm.kotlin": [".kotlin/"],
        "jvm.sbt-target": ["project/target/", "project/project/"],
        "jvm.scala-tools": [".bloop/", ".metals/"],
        "jvm.maven-target": ["target/"],
    },
    blocked_without={
        "jvm.gradle-build": ["build.gradle", "build.gradle.kts"],
        "jvm.gradle-project": ["build.gradle", "build.gradle.kts", "settings.gradle"],
        "jvm.idea-out": ["app.iml"],
        "jvm.kotlin": ["build.gradle", "build.gradle.kts"],
        "jvm.maven-target": ["pom.xml"],
        "jvm.sbt-target": ["build.sbt"],
        "jvm.scala-tools": [
            "build.sbt",
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
        ],
    },
)

CASES = [CASE]


class TestJvm(ProfileSuite):
    case = CASE
