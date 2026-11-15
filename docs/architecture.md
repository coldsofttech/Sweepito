# Architecture

This document records the design as implemented.

## Layers

The command line is a thin wrapper over a UI-free API: it parses options, calls
`api.py` (or the planner for `report`) and renders the result through `ui.py`. Nothing
below `cli/` prints or exits, so the same functions can be used as a library.

```text
src/sweepito/
  __init__.py       __version__ (the single source of the package version)
  __main__.py       python -m sweepito
  api.py            resolve_root, prepare, scan, clean
  config.py         config discovery, validation, merging with command line options
  registry.py       loads profiles/*.toml, merges custom profiles and rules
  planner.py        detect projects, match rules, apply safety gates, build the plan
  executor.py       deletes candidates; reports failures, never works around them
  git.py            wrappers around ls-files, check-ignore and rev-parse
  hooks.py          native Git hook install, uninstall, status
  models.py         Risk, Rule, Profile, Plan, Candidate, CleanResult, format_size
  errors.py         exception hierarchy and exit codes
  doctor.py         the checks behind `sweepito doctor`
  ui.py             Rich output (CLI only)
  cli/              command-line interface
    entry.py        main(): parse, dispatch, map errors to exit codes
    parser.py       argparse definition of every command and option
    commands.py     one cmd_* handler per command
    helpers.py      options, context, JSON output, confirmation, stderr console
  profiles/*.toml   built-in technology profiles (data, not code)
```

`errors.py` and `models.py` sit at the bottom and depend on nothing else in the
package. `git.py`, `config.py` and `registry.py` build on them; `planner.py` combines
the three, and `executor.py` applies a plan. `api.py` is the only module the CLI needs
for scanning and cleaning, and `hooks.py` and `doctor.py` use `git.py` and `api.py`.
`ui.py` renders `models.py` types and is imported only by the CLI.

## Imports and start-up

Imports are lazy: a module imports what it needs inside the function that uses it, and
annotation-only imports sit under `if TYPE_CHECKING:`. A name that a class body, a
default argument or a module constant needs when the module loads (a dataclass base,
`Risk` in a dataclass default, a compiled regular expression) stays at the top of its
module. This keeps `import sweepito` cheap and means a command pays only for the code it
runs:

- `sweepito --version` loads neither `rich` nor `pathspec`.
- `pathspec` is imported only when an exclude list or a glob rule needs it.
- `rich` is imported only by the first call in `ui.py` that draws something, so
  `--json` runs never load it.

`cli/__init__.py` re-exports `main` and `build_parser` as thin wrappers, so the
`sweepito.cli:main` entry point and `from sweepito.cli import main` stay valid without
importing the rest of the package. The dispatch module is called `entry.py`, not
`main.py`, so a submodule never shadows the re-exported function.

## Pipeline

1. **Inventory.** `git ls-files` gives non-ignored files (for marker detection) and
   ignored entries (the only things that may be cleaned).
2. **Detect.** Profiles activate from marker files; manual `--profile` wins.
3. **Match.** For each selected rule, find directories that contain its marker. Anchored
   literal targets are checked directly; other patterns are matched against ignored
   entries.
4. **Gate.** A candidate is dropped if it is excluded, escapes the root, is tracked (or
   holds tracked files), or is not ignored by Git. Nested candidates collapse into their
   parent.
5. **Execute or report.** Tracked state is re-read immediately before deleting.

## Commands and exit codes

Every handler in `cli/commands.py` takes the parsed `argparse.Namespace` and returns an
exit code; `cli/entry.py::main` is the only place that catches exceptions.

| Code | Meaning |
|---|---|
| `0` | Success, or nothing to clean |
| `1` | Some items failed, or `check` found candidates |
| `2` | Usage or configuration error (`ConfigError`) |
| `3` | Unexpected error |
| `4` | A safety gate refused the operation (`SafetyRefusal`) |
| `130` | Interrupted |

A `SweepitoError` carries its own `exit_code`; any other exception is reported as an
unexpected error. Errors are written to stderr through the shared Rich console.

## Configuration and profiles

- **Config** (`config.py`): `find_config` looks for `sweepito.toml`, `.sweepito.toml` or a
  `[tool.sweepito]` table in `pyproject.toml`, from the project root up to the Git root.
  `load_config` validates every section and key, and `merge` combines the command line
  and the file (command line wins, list options are combined).
- **Custom rules** are data: they never take a risk level or a command, always run, and
  go through the same gates as built-in rules. `validate_pattern` rejects patterns that
  could escape the root.
- **Registry** (`registry.py`): reads every `profiles/*.toml`, extends or adds profiles
  from the config, and rejects duplicate rule IDs.
- **Hooks** (`hooks.py`): writes a marked block into the hook file so it can be updated or
  removed without touching the rest of the hook.

## Tests

`tests/unit/` mirrors `src/sweepito/` with one `test_<module>.py` per module that holds
logic (`cli/` has one file per CLI module). `tests/integration/` runs the real commands
against temporary Git repositories: `test_<area>.py` for behavior across modules and
`profiles/test_<profile>.py` for each technology profile, built on `profiles/support.py`.
Everything under `tests/integration/` carries the `integration` marker, so
`pytest -m integration` and `pytest -m "not integration"` select either half. See
[development.md](development.md) for how to run them.

## Principles

- Safety by construction: the candidate set comes from Git's own ignore list.
- Rules are data, so adding a technology never changes the engine.
- The API has no UI dependency; the CLI renders results.
- Failures are collected and reported; the run continues with the other items.
- Imports are lazy, so a command loads only the code it uses.
