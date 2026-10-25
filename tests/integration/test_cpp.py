"""Integration tests for the cpp profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="cpp",
    profile="cpp",
    markers={"CMakeLists.txt": "", "build.ninja": "", "meson.build": ""},
    targets={
        "cpp.build": ["build/"],
        "cpp.clangd": [".cache/clangd/"],
        "cpp.cmake-build": ["cmake-build-debug/"],
        "cpp.cmake-in-source": ["CMakeCache.txt", "CMakeFiles/"],
        "cpp.ninja": [".ninja_log", ".ninja_deps"],
        "cpp.objects": ["main.o", "lib.a", "x.obj"],
    },
    blocked_without={
        "cpp.build": ["CMakeLists.txt", "build.ninja", "meson.build"],
        "cpp.cmake-build": ["CMakeLists.txt"],
        "cpp.cmake-in-source": ["CMakeLists.txt"],
        "cpp.ninja": ["build.ninja"],
    },
)

CASES = [CASE]


class TestCpp(ProfileSuite):
    case = CASE
