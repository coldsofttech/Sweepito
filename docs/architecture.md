# Architecture

This document records the design as implemented. The repository holds two implementations of
the same behaviour: the Python command line tool and a native JavaScript VS Code extension.

## Repository overview

```text
python/               the command line tool, its tests and the installers
extensions/vscode/    the VS Code extension (a port of the scan and clean pipeline)
brand/                logo and installer artwork
docs/                 documentation that covers the whole project
.github/              CI, security scans, release workflows and Dependabot
```

The components are built, tested, versioned and released independently, but they must behave
the same way. The Python package is the source of truth; the extension follows it, does not call
Python or the `sweepito` command, and needs only Git.

### What they share

| Shared | Source of truth | How the extension gets it |
|---|---|---|
| Profiles and rules | `python/src/sweepito/profiles/*.toml` | Converted to JSON at build time |
| Starter config | `python/src/sweepito/cli/templates/` | Copied at build time |
| Config file format | [configuration.md](configuration.md) | Reads the same files |
| Safety rules | planner, executor and git modules | Ported to JavaScript |
| Git hook block | `# >>> sweepito >>>` markers | Each tool replaces and removes the other's block |

A change to what is detected, matched or deleted belongs in both implementations, with tests on
each side. A new profile or rule only edits the TOML. The extension's differences from the
command line are listed in [vscode.md](vscode.md).

## Python package

The command line is a thin wrapper over a UI-free API: it parses options, calls the API and
renders the result. Nothing below `cli/` prints or exits.

```text
python/src/sweepito/
  api.py         scan and clean entry points used by the CLI
  planner.py     detects projects, matches rules, applies the safety gates
  executor.py    deletes candidates; reports failures, never works around them
  config.py      config discovery, validation and merging
  registry.py    loads the profiles and merges custom ones
  git.py         wrappers around the git binary
  hooks.py       native Git hook install, uninstall and status
  cli/           argument parsing, command handlers, error to exit-code mapping
  ui.py          Rich output (CLI only)
  profiles/      built-in technology profiles (data, not code)
```

`models.py` and `errors.py` sit at the bottom and depend on nothing else. `git.py`, `config.py`
and `registry.py` build on them, `planner.py` combines the three, and `executor.py` applies a
plan.

### Imports and start-up

Imports are lazy: a module imports what it needs inside the function that uses it, and
annotation-only imports sit under `if TYPE_CHECKING:`. Names needed when a module loads (a
dataclass base, a compiled regular expression) stay at the top. So `sweepito --version` loads
neither `rich` nor `pathspec`, and `--json` runs never load `rich`.

### Pipeline

The extension follows the same pipeline.

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

### Exit codes

Every command handler returns an exit code; `cli/entry.py` is the only place that catches
exceptions.

| Code | Meaning |
|---|---|
| `0` | Success, or nothing to clean |
| `1` | Some items failed, or `check` found candidates |
| `2` | Usage or configuration error |
| `3` | Unexpected error |
| `4` | A safety gate refused the operation |
| `130` | Interrupted |

### Configuration and profiles

- **Config** is found from the project root up to the Git root, validated key by key, and merged
  with the command line (command line wins, list options are combined).
- **Custom rules** are data: they never take a risk level or a command, always run, and go
  through the same gates as built-in rules. Patterns that could escape the root are rejected.
- **Registry** reads every profile, extends or adds profiles from the config, and rejects
  duplicate rule IDs.
- **Hooks** write a marked block into the hook file, so it can be updated or removed without
  touching the rest of the hook.

### Tests

`python/tests/unit/` mirrors the package, one test file per module with logic.
`python/tests/integration/` runs the real commands against temporary Git repositories, with one
test file per technology profile. Everything under `integration/` carries the `integration`
marker. See [development.md](development.md) for how to run them.

## VS Code extension

The extension is plain JavaScript with JSDoc types, bundled by esbuild into one file for the
extension and one for the Git hook script.

```text
extensions/vscode/
  src/extension.js   activation and wiring: commands, tree view, status bar
  src/core/          the scan and clean pipeline; no vscode imports
  src/hook-cli.js    entry point of the Git hook script
  scripts/           generates the bundled profiles from the Python package
```

`src/core/` mirrors the Python modules (planner, executor, git, config, registry, hooks), so the
logic can be unit tested without VS Code. Activation only registers things; each folder of a
multi-root workspace is scanned afterwards and keeps its own state. See [vscode.md](vscode.md) for
the layout and every difference from the command line tool.

Unit tests (Vitest) cover `src/core/`. Integration tests run in a real VS Code and cover commands,
views and the status bar.

## Builds and releases

- **CI** is one workflow with one required check, `ci`. A `changes` job finds which component a
  pull request touches and skips the other's jobs. Changes to the profiles or the config template
  also run the extension jobs.
- **Releases** start from a tag: `vX.Y.Z` releases the Python package and installers;
  `vscode-vX.Y.Z` releases the extension. The versions are independent, and each component keeps
  its own `CHANGELOG.md`.
- **Dependencies** are tracked per component (`python/uv.lock` and
  `extensions/vscode/package-lock.json`), with Dependabot, dependency review and audits for both.

## Principles

- Safety by construction: the candidate set comes from Git's own ignore list.
- Rules are data, so adding a technology never changes the engine, and both components get it.
- One behaviour, two implementations: the Python package leads and the extension follows.
- The core has no UI dependency: the CLI and the extension render the results.
- Failures are collected and reported; the run continues with the other items.
- Python imports are lazy, so a command loads only the code it uses.
