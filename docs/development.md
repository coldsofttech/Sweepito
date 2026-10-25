# Development

## Setup

```bash
uv sync
uv run pre-commit install
```

## Tasks

```bash
uv run pytest -n auto        # tests
uv run ruff check .          # lint
uv run ruff format .         # format
uv run sweepito scan         # try it on this repository
```

Tests create throwaway Git repositories. The symlink test is skipped where the OS does not
allow creating symlinks (for example Windows without developer mode).

## Adding a technology

Add `src/sweepito/profiles/<id>.toml` with `id`, `description`, `markers` and `[[rule]]`
entries (`id`, `paths`, `risk`, optional `requires`, `description`). Regenerate
`docs/profiles.md`, add a changelog line, and add a test with a fixture repository.
Never add rules that target application data, state files, secrets or IDE settings.

## Release

1. Update the version in `pyproject.toml` and `src/sweepito/__init__.py`.
2. Move `[Unreleased]` entries in `CHANGELOG.md` under the new version.
3. Push a `vX.Y.Z` tag. The release workflow checks the versions, runs lint and tests,
   publishes to PyPI with trusted publishing and creates a GitHub release.

PyPI trusted publishing requires this repository and a `pypi` environment to be registered as a
trusted publisher in the PyPI project settings. The Git tag is also what pre-commit users pin
with `rev:`.
