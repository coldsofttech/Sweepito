"""Integration tests for the swift profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="swift",
    profile="swift",
    markers={"MyApp.xcodeproj/project.pbxproj": "", "Package.swift": "", "Podfile": ""},
    targets={
        "swift.build": [".build/"],
        "swift.swiftpm": [".swiftpm/"],
        "xcode.pods": ["Pods/"],
        "xcode.xcuserdata": ["MyApp.xcodeproj/xcuserdata/"],
    },
    blocked_without={
        "swift.build": ["Package.swift"],
        "swift.swiftpm": ["Package.swift"],
        "xcode.pods": ["Podfile"],
        "xcode.xcuserdata": ["MyApp.xcodeproj/project.pbxproj"],
    },
)

CASES = [CASE]


class TestSwift(ProfileSuite):
    case = CASE
