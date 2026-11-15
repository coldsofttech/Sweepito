## What does this change?

<!-- A short description and the motivation. Link the issue if there is one. -->

## Safety check

- [ ] Only git-ignored, untracked paths inside the project root can be removed
- [ ] No new rule targets application data, state files, secrets or IDE settings
- [ ] Generic folder names use a `requires` marker and an anchored pattern

## Checklist

- [ ] Tests added or updated (new rules: `python/tests/integration/profiles/test_<profile>.py`)
- [ ] Python (from `python/`): `uv run pytest -n auto`, `ruff check .` and `ruff format --check .` pass
- [ ] VS Code extension (from `extensions/vscode/`): `npm run lint`, `npm run typecheck` and `npm run test:unit` pass
- [ ] The changelog of the component you changed is updated under `[Unreleased]` (`python/CHANGELOG.md` or `extensions/vscode/CHANGELOG.md`)
- [ ] Docs updated (`docs/profiles/` pages and the summary in `profiles.md` updated when profiles change)
- [ ] Works on Python 3.11
