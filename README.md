# Sweepito

[![Tests](https://github.com/coldsofttech/Sweepito/actions/workflows/tests.yml/badge.svg)](https://github.com/coldsofttech/Sweepito/actions/workflows/tests.yml)
[![Lint](https://github.com/coldsofttech/Sweepito/actions/workflows/lint.yml/badge.svg)](https://github.com/coldsofttech/Sweepito/actions/workflows/lint.yml)
[![Release](https://img.shields.io/github/v/release/coldsofttech/Sweepito?logo=github)](https://github.com/coldsofttech/Sweepito/releases)
[![PyPI](https://img.shields.io/pypi/v/sweepito?logo=pypi&logoColor=white)](https://pypi.org/project/sweepito/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/coldsofttech/Sweepito)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

Safely clean caches and build artifacts across languages, frameworks and tools.

## Why Sweepito?

Every ecosystem leaves its own clutter behind: `__pycache__/`, `.next/`, Cargo `target/`,
Gradle `build/`, `.terraform/`, `.ipynb_checkpoints/`, and many more. Cleaning them by hand
means remembering each tool's quirks, and the usual shortcuts are risky: `rm -rf build`
happily deletes a committed `build/` folder, and `git clean -fdx` removes everything
untracked, including your `.env`.

Sweepito is one tool for all of it, built around a simple rule: **it only removes paths that
Git already ignores and does not track, and only when the project's own marker files prove
what the folder is.** A `build/` directory is a candidate beside a `CMakeLists.txt` or
`pom.xml`, never because of its name alone.

## What you get

- **17 technology profiles and 97 rules**, detected automatically from marker files
  (`Cargo.toml`, `pom.xml`, `package.json`, ...). Repositories with several technologies and
  nested projects are handled per project.
- **Conservative by default.** Only `safe` caches are cleaned. Build output is opt-in, and
  dependency directories such as `node_modules/` need an explicit flag as well.
- **Previews you can trust.** `scan` shows exactly what `clean` would remove, with sizes and
  the reclaimable total.
- **One config format for every language**, with custom cleanup rules and profiles.
- **Git hooks**: post-commit cleanup through the `pre-commit` framework or a native hook,
  silent when there is nothing to do.
- **Machine-readable output** (`--json`) and meaningful exit codes for automation.
- **Small and cross-platform**: Python 3.11+, two dependencies (`pathspec`, `rich`), with a CI
  matrix covering Linux, macOS and Windows.

## Safety model

| Guarantee | How |
|---|---|
| Tracked files are never deleted | Candidates come from Git's own ignore list, and tracked paths are re-checked right before deleting |
| Nothing outside the project | Paths are resolved and confined to the project root; absolute paths and `..` are rejected |
| Links are not followed | Symlinks and Windows junctions are removed as links, never traversed |
| `.git/` is untouched | It is never a candidate |
| A name alone is not enough | A rule needs its marker file, and generic names are anchored beside it |
| Risky rules are opt-in | `high-impact` rules (dependencies, environments) never run unless you ask: `--enable RULE` or `--risk high-impact` |
| Not a Git repo? Refuse | Override only with `--no-git-check`, which counts as high impact |
| Failures are reported | Locked or protected files are listed and the run exits with code 1; nothing is forced |

Built-in rules never target application data, infrastructure state (`*.tfstate`), secrets
(`.env*`) or IDE settings.

## Install

Requires Python 3.11 or later and Git.

```bash
pipx install sweepito          # or: uv tool install sweepito
uvx sweepito scan              # run without installing
pip install sweepito           # into the current environment
```

## Quick start

```bash
sweepito scan                              # what would be removed (safe rules only)
sweepito scan --risk configurable          # include build output
sweepito clean                             # remove, asking first
sweepito clean --enable rust.target --yes  # also remove Cargo target/, no prompt
sweepito rules                             # list every rule and its risk
sweepito init                              # write a starter sweepito.toml
```

Example:

```
$ sweepito scan --risk configurable
Project: /home/dev/myapp   profiles: common, node, python, rust
                    Cleanup candidates
┌────────────────┬──────────────────┬──────────┬──────────────┐
│ Rule           │ Path             │     Size │ Risk         │
├────────────────┼──────────────────┼──────────┼──────────────┤
│ python.pytest  │ .pytest_cache/   │   3.2 KB │ safe         │
│ python.pycache │ src/__pycache__/ │  87.8 KB │ safe         │
│ node.next      │ web/.next/       │ 210.0 MB │ configurable │
│ rust.target    │ engine/target/   │   1.8 GB │ configurable │
└────────────────┴──────────────────┴──────────┴──────────────┘
4 candidate(s), 2.0 GB reclaimable.
Nothing deleted. Run 'sweepito clean' to remove them.
```

Output is rendered with [Rich](https://github.com/Textualize/rich) (tables, panels, colour).
Add `--json` for plain machine-readable output, or `--no-color` to turn colour off.

## Profiles

| Profile | Covers | Rules | Safe / configurable / high-impact |
|---|---|---:|---|
| `python` | Python, Django, Flask, FastAPI, pytest, Ruff, mypy, tox, coverage | 13 | 6 / 6 / 1 |
| `node` | Node.js, React, Next.js, Vue, Nuxt, Angular, Vite, Svelte, Astro | 15 | 8 / 6 / 1 |
| `node-pm` | npm, pnpm, Yarn, Bun project-local stores | 2 | 0 / 1 / 1 |
| `rust` | Rust and Cargo | 2 | 0 / 2 / 0 |
| `jvm` | Maven, Gradle, Kotlin, Spring Boot | 5 | 1 / 4 / 0 |
| `dotnet` | C#, F#, ASP.NET Core | 5 | 1 / 4 / 0 |
| `go` | Go modules and build tools | 3 | 1 / 1 / 1 |
| `cpp` | CMake, Make, Ninja, Meson | 6 | 1 / 5 / 0 |
| `php` | Composer, Laravel, Symfony | 7 | 2 / 4 / 1 |
| `ruby` | Bundler, Rails, Sinatra | 6 | 2 / 3 / 1 |
| `dart` | Dart and Flutter | 3 | 0 / 3 / 0 |
| `swift` | Swift Package Manager, Xcode | 4 | 0 / 3 / 1 |
| `elixir` | Mix and Phoenix | 6 | 3 / 2 / 1 |
| `r` | R, Shiny, renv, RMarkdown | 6 | 1 / 3 / 2 |
| `jupyter` | Notebooks and ML workflow outputs | 5 | 1 / 1 / 3 |
| `terraform` | Terraform and Terragrunt | 4 | 1 / 3 / 0 |
| `common` | OS and editor junk, generic logs (always active) | 5 | 2 / 3 / 0 |

The full list of targets, markers and risk levels is in [docs/profiles.md](docs/profiles.md).

### Risk levels

| Level | Behaviour |
|---|---|
| `safe` | On by default: well-identified caches that regenerate automatically |
| `configurable` | Opt-in: build output and other things that are slow to rebuild or mildly valuable |
| `high-impact` | Opt-in with `--enable RULE` or `--risk high-impact`: dependencies, environments, experiment data |
| `custom` | Rules you write yourself: always on, since you chose them. `--risk custom` runs only these |

## Use

Selection options work the same for `scan`, `clean`, `check` and `report`:

```bash
sweepito clean -p python -p node                       # only these profiles
sweepito clean --risk configurable -x dist/            # build output, but keep dist/
sweepito clean --enable node.modules
sweepito clean --disable python.hypothesis
sweepito scan --json | jq '.total_bytes'               # for scripts
sweepito check --quiet                                 # exit 1 if anything is left
```

## Configuration

Create `sweepito.toml` (or a `[tool.sweepito]` table in `pyproject.toml`). The format is the
same for every language, so non-Python projects need no `pyproject.toml`.

```toml
[defaults]
profiles = ["auto"]            # or ["python", "node"]
risk = "safe"                  # custom | safe | configurable | high-impact

[clean]
enable  = ["rust.target", "node.next"]
disable = ["python.hypothesis"]
exclude = ["dist/", "build/keep-me/"]   # gitignore syntax; always wins

[hook]                         # applies to hook runs only
quiet = true

[[rule]]                       # custom cleanup
id = "custom.test-output"
paths = ["test-results/", "tmp/e2e/**"]
```

Rules you write yourself always run and are shown as `custom`, so there is no risk level to
choose. Precedence is command line, then config file, then profile defaults, then built-in defaults.
Custom rules follow the same safety gates, so a target must still be inside the project,
untracked and git-ignored (or opt out of the ignore check per rule with
`allow_untracked = true`, which never applies to tracked files). Details are in
[docs/configuration.md](docs/configuration.md).

## Command line

| Command | Purpose |
|---|---|
| `scan` | List cleanup candidates with sizes (never deletes) |
| `clean` | Delete candidates (`-n` dry run, `-y` skip the prompt, `--non-interactive` for automation) |
| `check` | Like `scan`, but exits 1 if candidates exist |
| `report` | Reclaimable space by profile, rule and risk |
| `profiles` | List the supported technologies and what detects them (`--explain NAME` for one) |
| `rules` | List every cleanup rule and its risk (`--explain RULE` for one) |
| `config show` / `validate` | Show the effective settings or validate the file |
| `init` | Write a starter `sweepito.toml` |
| `hook install` / `uninstall` / `status` | Manage the native Git hook |
| `doctor` | Diagnose Git, config and hooks |

Run `sweepito <command> --help` for every option, or read [docs/cli.md](docs/cli.md).

## Git hook setup

With the [pre-commit](https://pre-commit.com) framework, add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/coldsofttech/Sweepito
    rev: v0.1.0
    hooks:
      - id: sweepito-clean     # post-commit cleanup
      # - id: sweepito-scan    # report-only at pre-commit
```

```bash
pre-commit install --hook-type post-commit
```

Without the framework, run `sweepito hook install` (add `--stage pre-commit` for the report-only
variant). It writes `.git/hooks/post-commit`, appends to an existing hook instead of replacing
it, and `sweepito hook uninstall` removes only its own block.

Hooks read the same `sweepito.toml` and honour the `[hook]` section. A post-commit hook cannot
fail a commit; if cleanup fails, it prints a message to stderr.

## Output, logs and exit codes

Sweepito does not write log files. Results go to standard output and problems to standard
error, so you can redirect them yourself.

- `--json` prints one JSON document with the candidates, skipped paths (and why), removed and
  failed items, and freed bytes.
- `-v` explains why paths were skipped, and `-q` prints nothing unless something needs
  attention. Hook runs are quiet when there is nothing to clean.
- `sweepito doctor` shows the environment, the config in use and installed hooks.

| Code | Meaning |
|---|---|
| 0 | Success, including "nothing to clean" |
| 1 | Some items failed or were skipped (for `check`: candidates exist) |
| 2 | Usage or configuration error |
| 3 | Unexpected error |
| 4 | Safety refusal (not a Git repo, high-impact without the flag, no consent) |
| 130 | Interrupted |

## Development setup

```bash
git clone https://github.com/coldsofttech/Sweepito
cd Sweepito
uv sync                       # uses Python 3.11, the minimum supported version
uv run pre-commit install
uv run pytest -n auto
uv run ruff check . && uv run ruff format --check .
```

See [docs/development.md](docs/development.md) and [docs/architecture.md](docs/architecture.md).

## Documentation

[CLI](docs/cli.md) · [Configuration](docs/configuration.md) · [Profiles and rules](docs/profiles.md) ·
[Architecture](docs/architecture.md) · [Development](docs/development.md) · [Changelog](CHANGELOG.md)

## Contributing

Contributions are welcome, especially new technologies and rules. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) first; every change keeps the safety invariants and comes
with tests. Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Because Sweepito deletes files, a bug that removes tracked files, anything outside the project
or follows a symlink is a security issue. Please report it privately as described in
[SECURITY.md](SECURITY.md) and do not open a public issue.

## License

[MIT](LICENSE)
