"""Integration tests for the python profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="python",
    profile="python",
    markers={"manage.py": "", "pyproject.toml": "[project]\nname='x'\n"},
    targets={
        "django.static": ["staticfiles/"],
        "python.build": ["build/"],
        "python.coverage": [".coverage", ".coverage.123", "htmlcov/", "coverage.xml"],
        "python.dist": ["dist/"],
        "python.eggs": [".eggs/", "src/pkg.egg-info/"],
        "python.hypothesis": [".hypothesis/"],
        "python.mypy": [".mypy_cache/", ".dmypy.json"],
        "python.pycache": ["pkg/__pycache__/", "mod.pyc"],
        "python.pytest": [".pytest_cache/"],
        "python.ruff": [".ruff_cache/"],
        "python.tox": [".tox/", ".nox/"],
        "python.typecheckers": [".pyre/", ".pytype/"],
        "python.venv": [".venv/", "venv/", "env/"],
    },
    blocked_without={"django.static": ["manage.py"]},
)

CASES = [CASE]


class TestPython(ProfileSuite):
    case = CASE
