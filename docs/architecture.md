# Architecture

## Modules (`src/sweepito/`)

| Module | Role |
|---|---|
| `cli.py` | argparse commands, exit codes, JSON output. A thin wrapper over the API |
| `api.py` | UI-free entry points: `resolve_root`, `prepare`, `scan`, `clean` |
| `config.py` | Config discovery, validation, merging with command line options |
| `registry.py` | Loads `profiles/*.toml`, merges custom profiles and rules |
| `planner.py` | Detect projects, match rules, apply safety gates, build the plan |
| `executor.py` | Deletes candidates; reports failures, never works around them |
| `git.py` | Wrappers around `git ls-files`, `check-ignore` and `rev-parse` |
| `hooks.py` | Native Git hook install, uninstall, status |
| `models.py`, `errors.py` | Shared types, exit-code-bearing exceptions |
| `ui.py`, `doctor.py` | Rich output (CLI only), diagnostics |
| `profiles/*.toml` | Built-in technology profiles (data, not code) |

## Pipeline

1. **Inventory.** `git ls-files` gives non-ignored files (for marker detection) and ignored
   entries (the only things that may be cleaned).
2. **Detect.** Profiles activate from marker files; manual `--profile` wins.
3. **Match.** For each selected rule, find directories that contain its marker. Anchored
   literal targets are checked directly; other patterns are matched against ignored entries.
4. **Gate.** A candidate is dropped if it is excluded, escapes the root, is tracked (or holds
   tracked files), or is not ignored by Git. Nested candidates collapse into their parent.
5. **Execute or report.** Tracked state is re-read immediately before deleting.

## Principles

- Safety by construction: the candidate set comes from Git's own ignore list.
- Rules are data, so adding a technology never changes the engine.
- The API has no UI dependency; the CLI renders results.
- Failures are collected and reported; the run continues with the other items.
