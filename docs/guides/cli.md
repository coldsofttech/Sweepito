# Command line guide

```text
sweepito [--version] <command> [options] [PATH]
```

| Command | What it does |
|---|---|
| `sweepito scan` | List what would be cleaned, with sizes. Deletes nothing |
| `sweepito clean` | Delete the cleanup candidates, after asking |
| `sweepito check` | Like `scan`, but exits 1 if anything is left to clean. For CI and hooks |
| `sweepito report` | Summarise reclaimable space by profile, rule and risk level |
| `sweepito rules` | List the rules, or describe one with `--explain` |
| `sweepito profiles` | List the technology profiles, or describe one with `--explain` |
| `sweepito config` | Show the effective settings (`show`) or validate the config (`validate`) |
| `sweepito init` | Write a starter `sweepito.toml` |
| `sweepito hook` | Install, remove or inspect the native Git hook |
| `sweepito doctor` | Check that Git, the project and your settings are ready. Changes nothing |

Add `--help` for the options of any command. Run a command inside a Git repository, or point
at one with `PATH`.

## How a run works

1. Sweepito asks Git for the files it ignores. Only those can ever be cleaned.
2. It detects which technologies the project uses from their marker files (for example
   `Cargo.toml` for `rust`), or uses the profiles you chose with `--profile`.
3. It matches the selected rules against the ignored files and drops every path that is
   excluded, tracked, outside the project root or not ignored by Git.
4. `scan` prints what is left. `clean` asks for confirmation, then deletes it, re-reading
   Git's tracked state first.

By default only `safe` rules run. Build output (`configurable`) and dependency folders
(`high-impact`) are opt-in. See the [README](../../README.md#safety-model) for the safety model.

## Concepts

| Term | Meaning |
|---|---|
| **Project root** | The `PATH` argument if given. Otherwise the Git root of the current directory, or the current directory if it is not in a Git repository |
| **Profile** | A technology (`python`, `node`, `rust`, ...). With the default `auto`, a profile is active when its marker files exist |
| **Rule** | One cleanup target with an ID such as `python.pycache`, a risk level and a marker requirement |
| **Risk level** | `safe` (on by default), `configurable` (opt-in), `high-impact` (opt-in), or `custom` for rules you define (always on) |
| **Candidate** | A path a selected rule matched that passed every safety check |
| **Skipped** | A matched path that was protected. Shown with `-v` |

## Exit codes

| Code | Meaning | Examples |
|---|---|---|
| 0 | Success, including "nothing to clean" and declining the prompt | |
| 1 | Some items failed; `check` found candidates; a required `doctor` check failed | Access denied on a locked file |
| 2 | Usage or configuration error | Unknown rule or profile, invalid config, missing `--config` file |
| 3 | Unexpected error | A bug; please report it |
| 4 | Safety refusal | Not a Git repository, no consent in a non-interactive `clean`, `init` over an existing file |
| 130 | Interrupted | Ctrl+C |

Errors are printed to stderr as `sweepito: error: <message>`.

## Options

### Global options (every command)

| Option | Default | What it does |
|---|---|---|
| `--config FILE` | discovered | Use this config file and skip the upward search. Exit 2 if it does not exist |
| `--json` | off | Print one JSON document on stdout instead of formatted output |
| `-q`, `--quiet` | off | Print nothing unless something needs attention |
| `-v`, `--verbose` | off | Also list skipped paths and the reason for each |
| `--no-color` | off | Plain output with no colour |
| `--version` | | Print the version and exit (before the command) |

### Selection options (`scan`, `clean`, `check`, `report`)

| Option | Default | What it does |
|---|---|---|
| `PATH` | Git root or cwd | Project root |
| `-p`, `--profile NAME` | auto | Use only this profile. Repeat for several. Unknown names exit 2 |
| `--enable RULE` | none | Turn a rule on regardless of its risk level. Repeatable. Unknown IDs exit 2 |
| `--disable RULE` | none | Turn a rule off. Repeatable. **Wins over `--enable`** |
| `-x`, `--exclude PATTERN` | none | Never touch paths matching this gitignore-style pattern. Repeatable. Always wins |
| `--risk LEVEL` | `safe` | Highest risk level to include: `safe`, `configurable` or `high-impact`. Your own rules are always included, and `custom` selects only them |
| `--no-git-check` | off | Allow use outside a Git repository. Nothing can be verified as ignored, so treat it as high impact |

List options from the command line are **combined** with the config file's lists. A scalar
option such as `--risk` **overrides** the file. Precedence: command line, then config file,
then profile defaults, then built-in defaults.

### `clean`

| Option | Default | What it does |
|---|---|---|
| `-n`, `--dry-run` | off | Same as `scan`: show the plan and delete nothing |
| `-y`, `--yes` | off | Do not ask for confirmation |
| `--non-interactive` | off | Never prompt; proceed with the configured rules. For scripts and hooks |

In a terminal, `clean` shows the plan and asks `[y/N]`. Without a terminal it refuses (exit 4)
unless `--yes` or `--non-interactive` is given. Locked or protected files are reported and the
run exits 1; nothing is forced.

### `rules` and `profiles`

| Option | Applies to | What it does |
|---|---|---|
| `PATH` | both | Project root, so custom rules and profiles from its config are included |
| `-p`, `--profile NAME` | `rules` | Only rules of this profile. Repeatable |
| `--risk LEVEL` | `rules` | Only rules at exactly this risk level |
| `--explain ID` | both | Describe one rule (`rules`) or one profile (`profiles`) |

### `hook`

```text
sweepito hook install   [--stage post-commit|pre-commit] [PATH]
sweepito hook uninstall [--stage post-commit|pre-commit] [PATH]
sweepito hook status    [PATH]
```

| Stage | Runs | Effect |
|---|---|---|
| `post-commit` (default) | After each commit | `sweepito clean --hook --non-interactive --quiet` |
| `pre-commit` | Before each commit | `sweepito scan --hook --quiet`. Reports only, never deletes |

The hook is a marked block appended to an existing hook file, so `uninstall` removes only its
own lines. Hooks need a Git repository and never block a commit. They read the same config and
apply its `[hook]` section.

### `init`

| Option | Default | What it does |
|---|---|---|
| `--force` | off | Overwrite an existing `sweepito.toml` |

`init` writes `sweepito.toml` in the project root, with a comment naming the profiles it
detected. It refuses (exit 4) if the file exists.

## Config file

Sweepito looks for `sweepito.toml`, `.sweepito.toml`, or a `[tool.sweepito]` table in
`pyproject.toml`, from the project root up to the Git root. `--config` skips the search.
Non-Python projects need no `pyproject.toml`.

```toml
[defaults]
profiles = ["auto"]            # or an explicit list, e.g. ["python", "node"]
risk = "safe"                  # custom | safe | configurable | high-impact

[clean]
enable = ["rust.target"]
disable = ["python.hypothesis"]
exclude = ["dist/", "build/keep-me/"]

[hook]
risk = "safe"                  # ceiling for hook runs
quiet = true

[[rule]]                       # a custom rule
id = "custom.test-output"
paths = ["test-results/", "tmp/e2e/**"]
```

Custom rules always run, show as `custom`, and follow the same safety gates as built-in rules.
They take no `risk` and no command. See the [configuration guide](configuration.md) for every
key. Check the result with `sweepito config show` and `sweepito config validate`.

## doctor

`sweepito doctor` prints one row per check and changes nothing.

| Check | Required | Passes when |
|---|---|---|
| Sweepito, pathspec, rich | pathspec and rich | The package and its dependencies are installed |
| Python | yes | Version 3.11 or newer |
| Git | yes | `git` is on `PATH` |
| Project root | yes | The path is a directory |
| Configuration | yes | The config file loads (or none is found: built-in defaults) |
| Risk ceiling, Git repository | no | Shows the effective ceiling and whether the root is a repository |
| Profiles | no | Detection ran |
| post-commit hook, pre-commit hook | no | The hook block is installed |

It exits 1 if any required check failed and 0 otherwise. A missing hook does not fail it.

## File patterns

`--exclude`, `[clean] exclude` and custom rule `paths` use gitignore syntax:

| Pattern | Matches |
|---|---|
| `dist/` | A directory named `dist` at any depth |
| `/dist/` | Only `dist` at the project root |
| `*.log` | Any file ending in `.log` |
| `tmp/e2e/**` | Everything below `tmp/e2e` |

Patterns that are empty, start with `!`, `#`, `~` or `//`, contain `..` or a backslash, or start
with a drive letter (`C:`) are rejected. A custom rule target must still be inside the project, untracked and git-ignored.

## JSON output

`scan`, `clean --dry-run` and `check` print:

| Field | Meaning |
|---|---|
| `root` | Absolute project root |
| `profiles` | Active profile IDs |
| `candidates[]` | `rule`, `profile`, `risk`, `path` (posix, relative to root), `is_dir`, `size` (bytes) |
| `skipped[]` | `path`, `rule`, `reason` |
| `total_bytes` | Sum of candidate sizes |
| `dry_run` | `true` for `scan`, `check` and `clean --dry-run` |

`clean` adds `removed[]` (same shape as `candidates`), `failed[]` (`path`, `error`) and
`freed_bytes`. `report` prints `root`, `total_bytes` and the `profile`, `rule` and `risk`
groupings, each with `count` and `bytes`. `--json` writes the document to stdout and
diagnostics to stderr, so it is safe to pipe:

```bash
sweepito scan --json | jq '.candidates[] | select(.size > 1000000) | .path'
sweepito clean --yes --json | jq '.freed_bytes'
```

## Recipes

```bash
# Weekly local tidy-up: safe caches plus build output, keep dist/
sweepito clean --risk configurable -x dist/ --yes

# Only free space in one technology
sweepito clean -p rust --enable rust.target --yes

# See which opt-in rules would reclaim the most, then enable the best
sweepito report
sweepito rules --explain rust.target

# Fail CI if caches were left in the working tree by a build step
sweepito check --quiet

# Reset a node project completely (dependencies too)
sweepito clean -p node --enable node.modules --yes

# Validate config in a pre-commit hook
sweepito config validate
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `... is not inside a Git repository` (exit 4) | Run it inside a repository, or pass `--no-git-check` knowing nothing can be verified as ignored |
| A folder you expected is not listed | It may not be git-ignored. Add it to `.gitignore`, or define a custom rule with `allow_untracked = true`. Check `sweepito scan -v` for a skip reason and `sweepito rules --explain RULE` for its marker requirement |
| `Confirmation required but no terminal is attached` | Add `--yes` (explicit) or `--non-interactive` (automation) |
| `Unknown rule ID(s)` | Run `sweepito rules` for the list. IDs are case-sensitive and contain a dot |
| A rule seems to match nothing | Its marker file must exist beside (or above) the folder. `build/` needs for example `CMakeLists.txt`, `pom.xml` or `build.gradle`, depending on the rule |
| Hook ran but nothing happened | Hooks are quiet by design. Run `sweepito scan -v` by hand, and `sweepito doctor` to check the hook is installed and `sweepito` is on `PATH` |
