"""Integration tests for the python profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="python",
    profile="python",
    markers={
        "manage.py": "",
        "conf.py": "",
        "mkdocs.yml": "",
        "pixi.toml": "",
        "pdm.lock": "",
        "pyproject.toml": "[project]\nname='x'\n"},
    targets={
        "django.static": ["staticfiles/"],
        "python.build": ["build/"],
        "python.coverage": [".coverage", ".coverage.123", "htmlcov/", "coverage.xml"],
        "python.dist": ["dist/"],
        "python.eggs": [".eggs/", "src/pkg.egg-info/"],
        "python.hypothesis": [".hypothesis/"],
        "python.mypy": [".mypy_cache/", ".dmypy.json"],
        "python.pdm": [".pdm-python", ".pdm-build/"],
        "python.pixi": [".pixi/"],
        "python.pycache": ["pkg/__pycache__/", "mod.pyc"],
        "python.mkdocs": ["site/"],
        "python.pylint": [".pylint.d/"],
        "python.pytest": [".pytest_cache/"],
        "python.ruff": [".ruff_cache/"],
        "python.sphinx": ["_build/"],
        "python.tox": [".tox/", ".nox/"],
        "python.typecheckers": [".pyre/", ".pytype/"],
        "python.venv": [".venv/", "venv/", "env/"],
    },
    blocked_without={
        "django.static": ["manage.py"],
        "python.mkdocs": ["mkdocs.yml"],
        "python.pdm": ["pdm.lock"],
        "python.pixi": ["pixi.toml"],
        "python.sphinx": ["conf.py"],
    },
)

CASES = [CASE]


class TestPython(ProfileSuite):
    case = CASE
