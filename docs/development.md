# Development

## Setup

```bash
uv sync                          # creates .venv with the dev tools
uv run pre-commit install        # lint, type check and unit tests before every commit
```

The layout of the code is described in [architecture.md](architecture.md). Tests live in
`tests/`, with `tests/unit/` mirroring `src/sweepito/`; see [Tests](#tests) below.

## Common tasks

```bash
uv run pytest -m "not integration" -n auto   # unit tests
uv run pytest -m integration -n auto         # integration tests, against real Git repositories
uv run ruff check .                          # lint
uv run ruff format .                         # format
uv run mypy                                  # type check
uv run sweepito scan                         # try it on this repository
```

Tests create throwaway Git repositories. The symlink test is skipped where the OS does not
allow creating symlinks (for example Windows without developer mode).

## Imports

Imports are lazy: a module imports what it needs inside the function that uses it, and
annotation-only imports sit under `if TYPE_CHECKING:`. A name needed when the module loads
(a base class, a compiled regular expression, a dataclass field default, a module constant)
stays at the top of its module. Never import lazily to hide a circular import; fix the
layering instead. Tests that patch a standard library module should patch the module itself
(for example `subprocess`), not an attribute of the module under test, because the import
happens inside the function.

## Adding a technology

Add `src/sweepito/profiles/<id>.toml` with `id`, `description`, `markers` and `[[rule]]`
entries (`id`, `paths`, `risk`, optional `requires`, `description`). Add
`docs/profiles/<id>.md` and a row in the summary of `docs/profiles.md`, add a changelog line, and add `tests/integration/profiles/test_<id>.py`
with a fixture repository (see `tests/integration/profiles/support.py`). Never add rules that
target application data, state files, secrets or IDE settings.

## Tests

Tests are marked, so you can pick what to run:

| Command | What runs |
| --- | --- |
| `uv run pytest` | Everything |
| `uv run pytest -m "not integration"` | Unit tests only (fast; what pre-commit runs) |
| `uv run pytest -m integration` | Integration tests in `tests/integration/` |

Unit tests live in `tests/unit/` and mirror `src/sweepito/`: a test for `planner.py` goes in
`tests/unit/test_planner.py`, and one for `cli/parser.py` in `tests/unit/cli/test_parser.py`.
Shared fixtures (the `repo` fixture and its `Repo` helper) are in `tests/conftest.py`.

Integration tests run the real commands against temporary Git repositories, so they need
only Git. They cover behavior across modules (`test_clean.py`, `test_output.py`,
`test_config.py`, ...) and one `profiles/test_<profile>.py` per technology. Everything under
`tests/integration/` is marked `integration` automatically in `tests/conftest.py`, so new
tests there need no decorator. Markers are registered in `pyproject.toml` and
`--strict-markers` is on, so a typo in a marker name is an error.

The `tests.yml` workflow and local runs can use `pytest-xdist` (`-n auto`, one worker per
CPU core). Leave it off when debugging a single test, since output and breakpoints are
easier without workers.

## Lint and type check

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

mypy runs in strict mode on `src/` (configured in `pyproject.toml`), so add type hints to
all new code.

## Pre-commit

`.pre-commit-config.yaml` runs these hooks on each commit:

- file hygiene from `pre-commit-hooks` (trailing whitespace, end-of-file, LF line endings,
  YAML and TOML syntax, merge-conflict markers, large files);
- `ruff check --fix` and `ruff format`;
- `markdownlint-cli2`, configured in `.markdownlint-cli2.yaml`;
- `mypy` on `src/`;
- the unit tests (`pytest tests/unit`).

Integration tests are left to CI. Run the hooks on everything with
`uv run pre-commit run --all-files`, and bump hook versions with
`uv run pre-commit autoupdate`.

## GitHub workflows

| Workflow | When | What |
| --- | --- | --- |
| `lint.yml` | Pushes to `main`, pull requests | `ruff check` and `ruff format --check` |
| `tests.yml` | Pushes to `main`, pull requests | Unit tests, then integration tests, on Ubuntu with Python 3.11, 3.12, 3.13, 3.14 and 3.15, and on Windows and macOS with 3.11 |
| `release.yml` | Pushing a tag like `v0.2.0` | Checks the tag against `__version__`, re-runs lint and tests, builds with `uv build`, publishes to PyPI and creates a GitHub release |

## Releasing

1. Choose the version with [Semantic Versioning](https://semver.org/). Update
   `__version__` in `src/sweepito/__init__.py`; it is the only place the version lives, and
   `pyproject.toml` reads it (`dynamic = ["version"]`).
2. Move the `[Unreleased]` entries in `CHANGELOG.md` under the new version.
3. Commit and push to `main`.
4. Tag and push the tag:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

The release workflow checks the tag against `__version__`, runs lint and tests, publishes
to PyPI with trusted publishing (no API token is stored) and creates a GitHub release.
Trusted publishing requires this repository, the workflow `release.yml` and the `pypi`
environment to be registered as a trusted publisher in the PyPI project settings. The Git
tag is also what pre-commit users pin with `rev:`.
