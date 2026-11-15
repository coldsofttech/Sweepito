# Development

The repository has two components that are developed and released separately: the Python command
line tool in `python/` and the VS Code extension in `extensions/vscode/`. The layout is described
in [architecture.md](architecture.md). Run each component's commands from its own folder.

## Setup

```bash
# Python (needs uv)
cd python
uv sync                          # creates .venv with the dev tools

# VS Code extension (needs Node, see extensions/vscode/.nvmrc)
cd extensions/vscode
npm ci                           # installs the locked dependencies

# Once, from the repository root: lint, type check and unit tests before every commit
uv run --project python pre-commit install
```

## Common tasks

Python, from `python/`:

```bash
uv run pytest -m "not integration" -n auto   # unit tests
uv run pytest -m integration -n auto         # integration tests, against real Git repositories
uv run ruff check .                          # lint
uv run ruff format .                         # format
uv run mypy                                  # type check
uv run sweepito scan                         # try it on this repository
```

VS Code extension, from `extensions/vscode/`:

```bash
npm run lint                     # lint (also: format:check, typecheck)
npm run test:unit                # unit tests (Vitest)
npm run build                    # bundle to dist/
npm run test:integration         # needs a display or xvfb; downloads VS Code the first time
npm run package                  # build the .vsix
```

To try the extension, open `extensions/vscode` in VS Code and press F5 to launch an Extension
Development Host.

Tests create throwaway Git repositories. The symlink test is skipped where the OS does not
allow creating symlinks (for example Windows without developer mode).

## Python

### Imports

Imports are lazy: a module imports what it needs inside the function that uses it, and
annotation-only imports sit under `if TYPE_CHECKING:`. A name needed when the module loads
(a base class, a compiled regular expression, a dataclass field default, a module constant)
stays at the top of its module. Never import lazily to hide a circular import; fix the
layering instead. Tests that patch a standard library module should patch the module itself
(for example `subprocess`), not an attribute of the module under test, because the import
happens inside the function.

### Tests

Tests are marked, so you can pick what to run:

| Command | What runs |
| --- | --- |
| `uv run pytest` | Everything |
| `uv run pytest -m "not integration"` | Unit tests only (fast; what pre-commit runs) |
| `uv run pytest -m integration` | Integration tests in `tests/integration/` |

Unit tests mirror the package: a test for `planner.py` goes in `tests/unit/test_planner.py`,
and one for `cli/parser.py` in `tests/unit/cli/test_parser.py`. Integration tests run the real
commands against temporary Git repositories, so they need only Git, with one
`profiles/test_<profile>.py` per technology. Everything under `tests/integration/` is marked
`integration` automatically, so new tests there need no decorator. Markers are registered in
`pyproject.toml` and `--strict-markers` is on, so a typo in a marker name is an error.

CI and local runs can use `pytest-xdist` (`-n auto`). Leave it off when debugging a single
test, since output and breakpoints are easier without workers.

### Lint and type check

`ruff` checks and formats the code, and `mypy` runs in strict mode on `src/` (configured in
`pyproject.toml`), so add type hints to all new code.

## VS Code extension

Keep `vscode` imports in `src/extension.js` and the files it wires up; put logic in `src/core/`
so it can be unit tested without VS Code. Unit tests are in `test/unit/` and mirror the source;
integration tests in `test/integration/` run in a real VS Code and are written as CommonJS
(`*.test.cjs`). The first integration run downloads VS Code, so while iterating run one unit
file with `npx vitest run test/unit/<file>`.

`npm run build` and `npm run test:unit` first regenerate the bundled profiles from the Python
package, so a profile change shows up after a rebuild. Add a command, view or setting in
`package.json` together with its documentation in the extension README and `[Unreleased]`
changelog entry.

## Adding a technology

Add `python/src/sweepito/profiles/<id>.toml` with `id`, `description`, `markers` and `[[rule]]`
entries (`id`, `paths`, `risk`, optional `requires` and `requires_all`, `description`). Choose
`risk` with the [risk levels](profiles.md#risk-levels), give each specialised rule its own
marker, and use `requires_all` when one marker is not enough evidence. Then:

- add `docs/profiles/<id>.md` and a row in the summary of `docs/profiles.md`;
- add `python/tests/integration/profiles/test_<id>.py` with a fixture repository (see
  `support.py` next to it);
- add a line under `[Unreleased]` in `python/CHANGELOG.md`.

The VS Code extension picks the profile up from the same file when it is rebuilt; nothing else
changes there. Never add rules that target application data, state files, secrets or IDE
settings.

## Pre-commit

`.pre-commit-config.yaml` at the repository root runs these hooks on each commit:

- file hygiene from `pre-commit-hooks` (trailing whitespace, end-of-file, LF line endings,
  YAML and TOML syntax, merge-conflict markers, large files);
- `ruff check --fix` and `ruff format`;
- `markdownlint-cli2`, configured in `.markdownlint-cli2.yaml`;
- `mypy` on the Python package;
- the Python unit tests.

Integration tests are left to CI. Run the hooks on everything with
`uv run --project python pre-commit run --all-files`, and bump hook versions with
`uv run --project python pre-commit autoupdate`.

## GitHub workflows

| Workflow | When | What |
| --- | --- | --- |
| `ci.yml` | Pushes to `main`, pull requests | Python: lint, unit and integration tests on Ubuntu with Python 3.11 to 3.15 and on Windows and macOS with 3.11, and a package build checked with `twine`. Extension: lint, unit tests on Node 22 to 26, integration tests on Linux, Windows and macOS, build and package. Only the component a pull request touches runs. The final `ci` job is the single required status check |
| `installers.yml` | Pull requests that touch the installers | Builds the Windows and Linux installers and checks that each installs, runs and uninstalls |
| `security.yml` | Pull requests, pushes to `main`, weekly | Semgrep static analysis for each component, reported to the Security tab |
| `dependency-review.yml` | Pull requests | Reviews dependency changes for known vulnerabilities |
| `audit.yml` | Lock file changes, weekly, manual | Audits the locked Python and npm dependencies |
| `release.yml` | Pushing a release tag | Releases one component; see below |

## Releasing

The two components have independent versions and changelogs, and each release starts from a tag:
`vX.Y.Z` for the Python package and installers, `vscode-vX.Y.Z` for the extension. Follow
[Semantic Versioning](https://semver.org/) for both.

### Python package and installers

1. Update `__version__` in `python/src/sweepito/__init__.py`; it is the only place the version
   lives, and `pyproject.toml` reads it (`dynamic = ["version"]`).
2. Move the `[Unreleased]` entries in `python/CHANGELOG.md` under the new version.
3. Commit and push to `main`.
4. Tag and push the tag:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

The release workflow checks the tag against `__version__`, runs lint and tests, builds the
installers, publishes to PyPI with trusted publishing (no API token is stored) and creates a
GitHub release with the package files and installers. Trusted publishing requires this
repository, the workflow `release.yml` and the `pypi` environment to be registered as a trusted
publisher in the PyPI project settings. The Git tag is also what pre-commit users pin with
`rev:`.

### VS Code extension release

1. Update `version` in `extensions/vscode/package.json`.
2. Move the `[Unreleased]` entries in `extensions/vscode/CHANGELOG.md` under the new version.
3. Commit and push to `main`, and wait for `ci` to pass on that commit.
4. Tag and push the tag:

   ```bash
   git tag vscode-v0.1.0
   git push origin vscode-v0.1.0
   ```

The release workflow checks the tag against `package.json` and that `ci` passed on the tagged
commit, builds the `.vsix` and attaches it to a GitHub release. It then waits for a reviewer to
approve the `vscode` environment before publishing to the Visual Studio Marketplace (trusted
publishing, no token).
