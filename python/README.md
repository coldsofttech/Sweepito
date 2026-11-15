# Sweepito

[![CI](https://github.com/coldsofttech/Sweepito/actions/workflows/ci.yml/badge.svg)](https://github.com/coldsofttech/Sweepito/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/sweepito?logo=pypi&logoColor=white)](https://pypi.org/project/sweepito/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/github/license/coldsofttech/Sweepito)](https://github.com/coldsofttech/Sweepito/blob/main/LICENSE)

Safely clean generated project artifacts (caches, build output, test reports and tool
leftovers) across languages, frameworks, game engines, data and infrastructure tooling.

Sweepito is a command-line tool: you install it and run `sweepito`. It is not a Python
library and has no Python API to import.

**It only removes paths that Git already ignores and does not track, and only when the
project's own marker files prove what the folder is.** A `build/` directory is a candidate
beside a `CMakeLists.txt` or `pom.xml`, never because of its name alone.

## Install

Requires Python 3.11 or later and [Git](https://git-scm.com/). Because Sweepito is a program
rather than a library, [pipx](https://pipx.pypa.io/) and [uv](https://docs.astral.sh/uv/) are
the best fit: they keep it out of your project environments, and your project does not need to
be a Python project.

```bash
pipx install sweepito          # or: uv tool install sweepito
uvx sweepito scan              # run once without installing
```

Check the install with `sweepito --version`, and your setup with `sweepito doctor`.

No Python? Download a native installer (`setup.exe` for Windows, `.deb` or `.rpm` for Linux)
from the [releases](https://github.com/coldsofttech/Sweepito/releases).

## Quick start

```bash
sweepito scan                              # what would be removed (safe rules only)
sweepito scan --risk configurable          # include build output
sweepito clean                             # remove, asking first
sweepito clean --enable rust.target --yes  # also remove Cargo target/, no prompt
sweepito rules                             # list every rule and its risk
sweepito init                              # write a starter sweepito.toml
```

## What you get

- **29 technology profiles**, detected automatically from marker files (`Cargo.toml`,
  `pom.xml`, `package.json`, ...), with nested projects handled per project.
- **Conservative by default.** Only `safe` caches are cleaned. Build output is opt-in, and
  dependency directories such as `node_modules/` need an explicit flag as well.
- **Previews you can trust.** `scan` shows exactly what `clean` would remove, with sizes.
- **One config format for every language**, with custom cleanup rules and profiles.
- **Git hooks** for post-commit cleanup, and `--json` output and exit codes for automation.
- **Linux, macOS and Windows**, on any project in a Git repository.

## VS Code

Prefer to stay in your editor? The
[Sweepito extension for VS Code](https://github.com/coldsofttech/Sweepito/blob/main/extensions/vscode/README.md)
runs on its own, so it needs neither Python nor this command line tool.

## Learn more

[Full documentation](https://github.com/coldsofttech/Sweepito#readme) ·
[Command line guide](https://github.com/coldsofttech/Sweepito/blob/main/python/docs/cli.md) ·
[Configuration](https://github.com/coldsofttech/Sweepito/blob/main/docs/configuration.md) ·
[Profiles and rules](https://github.com/coldsofttech/Sweepito/blob/main/docs/profiles.md) ·
[Changelog](https://github.com/coldsofttech/Sweepito/blob/main/python/CHANGELOG.md) ·
[Report an issue](https://github.com/coldsofttech/Sweepito/issues)

## License

[MIT](https://github.com/coldsofttech/Sweepito/blob/main/LICENSE)
