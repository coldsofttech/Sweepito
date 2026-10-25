# Contributing to Sweepito

Thanks for helping. Sweepito deletes files, so changes are reviewed with extra care for
safety.

## Getting started

```bash
uv sync
uv run pre-commit install
uv run pytest -n auto
uv run ruff check . && uv run ruff format --check .
```

Development uses **Python 3.11**, the minimum supported version (see `.python-version`).
Please do not use syntax or standard library features newer than 3.11. CI also runs 3.13 on
Linux, macOS and Windows.

More detail is in [docs/development.md](docs/development.md) and
[docs/architecture.md](docs/architecture.md).

## Ground rules

1. **Safety invariants are not negotiable.** Only git-ignored, untracked paths inside the
   project root may be removed. Symlinks are never followed. See the Security Policy for
   the full list. A change that weakens one needs a strong justification and tests.
2. **No rule may target** application data, infrastructure state (`*.tfstate`), secrets
   (`.env*`) or IDE settings.
3. **A folder name alone is never enough.** Generic names (`build/`, `bin/`, `dist/`) need
   a `requires` marker and an anchored (`/`) pattern.
4. **Tests come with every change.** Bug fixes need a regression test.
5. **Keep dependencies minimal.** Currently `pathspec` and `rich`.

## Adding or changing a rule

1. Edit `src/sweepito/profiles/<profile>.toml`.
2. Update the matching `tests/integration/test_<profile>.py`: add the targets, and for a
   rule with `requires` also list the marker files in `blocked_without`. The guard tests in
   `test_registry_coverage.py` fail if you forget.
3. Regenerate `docs/profiles.md` and add a line to `CHANGELOG.md` under `[Unreleased]`.

To add a whole new technology, add a new profile TOML and a matching test module.

## Pull requests

- Branch from `main`; keep the change focused.
- Make sure tests, Ruff and the format check pass locally.
- Describe the behaviour change and any risk to users' files.
- Fill in the pull request template.

By contributing you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md) and that your
contribution is licensed under the project's MIT license.
