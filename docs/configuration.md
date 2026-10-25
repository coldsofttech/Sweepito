# Configuration

Sweepito reads `sweepito.toml` or `.sweepito.toml`, or a `[tool.sweepito]` table in
`pyproject.toml`. It searches the current folder and then each parent, stopping at the Git
root. `--config FILE` or an explicit path skips the search.

Precedence: command line > config file > profile defaults > built-in defaults.
`enable`, `disable` and `exclude` lists from the file and the command line are combined.
`disable` always beats `enable`. Unknown sections, keys or values are an error (exit 2).
Keys accept dashes or underscores.

```toml
[defaults]
profiles = ["auto"]        # or ["python", "node"]; "auto" detects from marker files
risk = "safe"              # custom | safe | configurable | high-impact

[clean]
enable  = ["rust.target", "node.next"]
disable = ["python.hypothesis"]
exclude = ["dist/", "build/keep-me/"]   # gitignore syntax; always wins over any rule

[hook]                     # applies only to hook runs
risk = "safe"
quiet = true
```

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

**Risk.** Custom rules have no risk setting. A rule you write yourself is deliberate, so it always
has the level `custom`: it is always selected, in `scan`, `clean`, `check` and hooks alike, and
shown as `custom`. Adding a `risk` key to a `[[rule]]` is an error. To switch a rule off, remove it
or list its ID under `disable`. The safety checks below still apply. `custom` is also a valid value for the global
`risk` ceiling (`[defaults]`, `[hook]` or `--risk`): it selects only your custom rules and none of
the built-in ones, for example `[hook] risk = "custom"` limits hooks to your own cleanup.

Path syntax follows `.gitignore`: a leading `/` anchors the pattern to the directory with the
marker file, and other patterns match at any depth. Absolute paths, `..`, drive letters, `~`,
backslashes and negations are rejected.

Custom rules use the same safety gates as built-in ones: the target must be inside the
project, untracked, and git-ignored. For something that is not in `.gitignore`, either add it
there or set `allow_untracked = true` on the rule. That still never deletes tracked files.

Command rules (`exec`) are not supported yet and are rejected with an error.

## Custom profiles

```toml
[profile.team]
markers = ["team.marker"]          # profile is active when one of these files exists

[[rule]]
id = "team.out"
profile = "team"
paths = ["/out/"]
```

A profile without markers is always active.

## Risk levels

| Level | Behaviour |
|---|---|
| `safe` | On by default |
| `configurable` | Opt-in with `enable`, `--enable` or a higher `risk` |
| `high-impact` | Opt-in: `enable`, `--enable`, or `--risk high-impact` |
| `custom` | Rules you define yourself. Always on, with no setting; see above |

Built-in rules never target application data, infrastructure state (`*.tfstate`), secrets
(`.env*`) or IDE settings.
