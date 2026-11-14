# Configuration

Sweepito reads defaults from `sweepito.toml`, `.sweepito.toml`, or a `[tool.sweepito]` table
in `pyproject.toml`. Use `--config FILE` to read a different file and skip the search.
Precedence: command line, config file, profile defaults, built-in defaults. The `enable`,
`disable` and `exclude` lists from the file and the command line are combined, and `disable`
always beats `enable`. A scalar such as `risk` on the command line overrides the file.

A configuration file can never run a command: custom rules only list paths, and the
`exec` key is rejected. The safety checks apply to every rule, whether built in or custom.

## Where the file is found

Without `--config`, Sweepito starts at the project root (the `PATH` argument, else the Git
root of the current folder) and walks up to the Git root. In each folder it looks for, in
order:

1. `sweepito.toml`
2. `.sweepito.toml`
3. `pyproject.toml`, if it has a `[tool.sweepito]` table

The first match wins. Non-Python projects need no `pyproject.toml`. Run
`sweepito config show` to see which file is in use, and `sweepito config validate` to check
it. `sweepito init` writes a starter file.

## Keys

Keys accept dashes or underscores. Unknown sections, unknown keys and invalid values stop
the run with exit code 2 and a message naming the section.

```toml
# sweepito.toml
[defaults]
profiles = ["auto"]            # or ["python", "node"]; "auto" detects from marker files
risk = "safe"                  # custom | safe | configurable | high-impact

[clean]
enable = ["rust.target", "node.next"]
disable = ["python.hypothesis"]
exclude = ["dist/", "build/keep-me/"]   # gitignore syntax; always wins over any rule

[hook]                         # applies only to hook runs
risk = "safe"
quiet = true
```

The same settings in `pyproject.toml` go under `[tool.sweepito.*]`:

```toml
[tool.sweepito.defaults]
risk = "configurable"

[tool.sweepito.clean]
exclude = ["dist/"]
```

| Section | Key | Type | Meaning |
|---|---|---|---|
| `[defaults]` | `profiles` | list of strings | Profiles to use. `"auto"` detects them; names replace auto-detection |
| `[defaults]` | `risk` | string | Highest risk level to include: `custom`, `safe`, `configurable` or `high-impact` |
| `[clean]` | `enable` | list of strings | Rule IDs to turn on regardless of risk level |
| `[clean]` | `disable` | list of strings | Rule IDs to turn off. Wins over `enable` |
| `[clean]` | `exclude` | list of strings | Gitignore-style patterns that are never touched. Always wins |
| `[hook]` | `risk` | string | Risk ceiling for hook runs, instead of `[defaults] risk` |
| `[hook]` | `quiet` | true / false | Print only when something needs attention during hook runs |
| `[[rule]]` | | table | A custom path rule; see below |
| `[profile.NAME]` | | table | A custom profile; see below |

For the risk ceiling, the order is: `--risk`, then `[hook] risk` (hook runs only), then
`[defaults] risk`, then `safe`. Rule IDs and profile names are checked when a command runs,
so a typo in `enable`, `disable` or `profiles` exits 2 and names the unknown value.

## Custom path rules

```toml
[[rule]]
id = "custom.test-output"          # lowercase letters, digits, . _ -
paths = ["test-results/", "tmp/e2e/**"]
requires = ["package.json"]        # optional marker files; empty means project root
profile = "custom"                 # optional; groups the rule
description = "Test output"
allow_untracked = false            # see below
```

| Key | Type | Meaning |
|---|---|---|
| `id` | string | Required, unique. Lowercase letters, digits, `.`, `_` and `-` |
| `paths` | list of strings | Required, not empty. Gitignore-style patterns |
| `requires` | list of strings | Marker files that must exist beside the target. Empty means the project root |
| `profile` | string | Profile the rule is listed under (default `custom`) |
| `description` | string | Shown by `sweepito rules` |
| `allow_untracked` | true / false | Also match paths that are not git-ignored (default `false`) |

**Risk.** Custom rules have no risk setting. A rule you write yourself is deliberate, so it
always has the level `custom`: it is always selected by `scan`, `clean`, `check` and hooks,
and shown as `custom`. Adding a `risk` key to a `[[rule]]` is an error. To switch a rule off,
remove it or list its ID under `disable`. `custom` is also a valid value for the global
`risk` ceiling (`[defaults]`, `[hook]` or `--risk`): it selects only your custom rules and
none of the built-in ones, for example `[hook] risk = "custom"` limits hooks to your own
cleanup.

**Paths.** Syntax follows `.gitignore`: a leading `/` anchors the pattern to the folder with
the marker file, and other patterns match at any depth. Empty patterns, negations (`!`),
`#`, `~`, `..`, backslashes, drive letters and `//` prefixes are rejected.

**Safety.** Custom rules use the same gates as built-in ones: the target must be inside the
project, untracked and git-ignored. For something that is not in `.gitignore`, either add it
there or set `allow_untracked = true` on the rule. That still never deletes tracked files.

Command rules (`exec`) are not supported and are rejected with an error.

## Custom profiles

```toml
[profile.team]
markers = ["team.marker"]          # profile is active when one of these files exists
description = "Team build output"

[[rule]]
id = "team.out"
profile = "team"
paths = ["/out/"]
```

A profile without markers is always active. Naming an existing built-in profile extends it:
the markers are added to the built-in ones and a `description` replaces the built-in one.

## Risk levels

| Level | Behavior |
|---|---|
| `safe` | On by default |
| `configurable` | Opt-in with `enable`, `--enable` or a higher `risk` |
| `high-impact` | Opt-in with `enable`, `--enable` or `--risk high-impact` |
| `custom` | Rules you define yourself. Always on, with no setting; see above |

Built-in rules never target application data, infrastructure state (`*.tfstate`), secrets
(`.env*`) or IDE settings.
