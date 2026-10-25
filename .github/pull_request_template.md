## What does this change?

<!-- A short description and the motivation. Link the issue if there is one. -->

## Safety check

- [ ] Only git-ignored, untracked paths inside the project root can be removed
- [ ] No new rule targets application data, state files, secrets or IDE settings
- [ ] Generic folder names use a `requires` marker and an anchored pattern

## Checklist

- [ ] Tests added or updated (new rules: `tests/integration/test_<profile>.py`)
- [ ] `uv run pytest -n auto`, `ruff check .` and `ruff format --check .` pass
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Docs updated (`docs/profiles.md` is regenerated when profiles change)
- [ ] Works on Python 3.11
