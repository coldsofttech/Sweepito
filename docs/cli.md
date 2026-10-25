# Command line reference

```
sweepito [--version] <command> [options] [PATH]
```

- [Concepts](#concepts)
- [Options shared by commands](#options-shared-by-commands)
- Commands: [`scan`](#scan) · [`clean`](#clean) · [`check`](#check) · [`report`](#report) ·
  [`rules`](#rules) · [`profiles`](#profiles) · [`config`](#config) · [`init`](#init) · [`hook`](#hook) · [`doctor`](#doctor)
- [Output and colour](#output-and-colour) · [Exit codes](#exit-codes) · [JSON output](#json-output) ·
  [Recipes](#recipes) · [Troubleshooting](#troubleshooting)

Example output below uses a project at `/home/dev/demo`. Sizes are illustrative.

## Concepts

| Term | Meaning |
|---|---|
| **Project root** | The `PATH` argument if given. Otherwise the Git root of the current directory, or the current directory if it is not in a Git repository |
| **Profile** | A technology (`python`, `node`, `rust`, ...). With the default `auto`, a profile is active when its marker files exist (for example `Cargo.toml` for `rust`) |
| **Rule** | One cleanup target with an ID such as `python.pycache`, a risk level and a marker requirement. List them with `sweepito rules` |
| **Risk level** | `safe` (on by default), `configurable` (opt-in), `high-impact` (opt-in), or `custom` for rules you define yourself (always on) |
| **Candidate** | A path a selected rule matched that passed every safety check |
| **Skipped** | A matched path that was protected (excluded, tracked, or resolving outside the root). Shown with `-v` |

Safety checks applied to every candidate, whatever the command: it must be git-ignored and
untracked, inside the project root, not excluded, and (for built-in rules) its marker file must
exist. See the [README](../README.md#safety-model).

## Options shared by commands

### Global options (every command except `--version`)

| Option | Meaning |
|---|---|
| `--config FILE` | Use this config file and skip the upward search. Exit 2 if the file does not exist |
| `--json` | Print one JSON document on stdout instead of formatted output |
| `-q`, `--quiet` | Print nothing unless something needs attention |
| `-v`, `--verbose` | Also list skipped paths and the reason for each |
| `--no-color` | Plain output with no colour (tables keep their layout) |

### Selection options (`scan`, `clean`, `check`, `report`)

| Option | Meaning |
|---|---|
| `PATH` | Project root (default: Git root of the current directory) |
| `-p`, `--profile NAME` | Use only this profile. Repeat for several. Replaces auto-detection. Unknown names are exit 2 |
| `--enable RULE` | Turn a rule on regardless of its risk level. Repeatable. Unknown IDs are exit 2 |
| `--disable RULE` | Turn a rule off. Repeatable. **Wins over `--enable`** |
| `-x`, `--exclude PATTERN` | Never touch paths matching this gitignore-style pattern. Repeatable. Always wins |
| `--risk LEVEL` | Highest risk level to include: `safe` (default), `configurable`, `high-impact`. Your own rules are always included, and `custom` selects **only** them |
| `--no-git-check` | Allow use outside a Git repository. Nothing can be verified as ignored, so treat it as high impact |

List options from the command line are **combined** with the config file's lists. A scalar
option such as `--risk` **overrides** the file. Precedence: command line, then config file, then
profile defaults, then built-in defaults.

---

## `scan`

List what would be removed. Never deletes anything.

```
sweepito scan [PATH] [selection options] [--json] [-q] [-v] [--no-color]
```

```
$ sweepito scan
Project: /home/dev/demo   profiles: common, node, python, rust
                   Cleanup candidates
┌────────────────┬──────────────────┬──────┬──────┐
│ Rule           │ Path             │ Size │ Risk │
├────────────────┼──────────────────┼──────┼──────┤
│ python.pytest  │ .pytest_cache/   │  2 B │ safe │
│ python.pycache │ src/__pycache__/ │  9 B │ safe │
└────────────────┴──────────────────┴──────┴──────┘
2 candidate(s), 11 B reclaimable.
Nothing deleted. Run 'sweepito clean' to remove them.
```

The header shows the project root and the profiles that were activated. `common` is always
active. Only `safe` rules are selected by default, so build output such as `.next/` and
`target/` is not listed. Risk levels are coloured: `safe` green, `configurable` yellow,
`high-impact` red.

**Include more by raising the risk ceiling:**

```
$ sweepito scan --risk configurable
┌────────────────┬──────────────────┬─────────┬──────────────┐
│ Rule           │ Path             │    Size │ Risk         │
├────────────────┼──────────────────┼─────────┼──────────────┤
│ node.next      │ .next/           │  4.9 KB │ configurable │
│ python.pytest  │ .pytest_cache/   │     2 B │ safe         │
│ node.dist      │ dist/            │     2 B │ configurable │
│ python.pycache │ src/__pycache__/ │     9 B │ safe         │
│ rust.target    │ target/          │ 19.5 KB │ configurable │
└────────────────┴──────────────────┴─────────┴──────────────┘
5 candidate(s), 24.4 KB reclaimable.
```

**Only your own rules.** `custom` sits below `safe`, so `--risk custom` selects your custom rules
and none of the built-in ones. It works with `scan`, `clean`, `check` and `report`:

```bash
sweepito scan --risk custom
sweepito clean --risk custom --yes
```

**Include one specific rule:**

```bash
sweepito scan --enable rust.target
```

**See what was protected (`-v`).** A path that git tracks is never a candidate, even if a rule
matches it:

```
$ sweepito scan --enable rust.target -v
...
skipped target (rust.target): tracked by git
2 candidate(s), 11 B reclaimable. Skipped 1 protected path(s).
```

Skip reasons: `excluded by configuration`, `tracked by git`, `resolves outside the project root`.

**Exclude something:**

```
$ sweepito scan -x src/
...
│ python.pytest │ .pytest_cache/ │  2 B │ safe │
...
1 candidate(s), 2 B reclaimable. Skipped 1 protected path(s).
```

**Quiet mode** prints a single line only when there are candidates, and nothing otherwise. It is
what the pre-commit report hook uses:

```
$ sweepito scan --quiet
sweepito: 2 cleanup candidate(s), 11 B reclaimable (run 'sweepito scan').
```

**Select profiles explicitly:**

```bash
sweepito scan -p python -p node         # only these two; no auto-detection
sweepito scan /path/to/other/project    # a different project root
```

Exit code is 0 unless an error occurs (see [exit codes](#exit-codes)); `scan` does not fail
because candidates exist. Use [`check`](#check) for that.

---

## `clean`

Delete the candidates `scan` would list. Takes the same selection options as `scan`, plus:

| Option | Meaning |
|---|---|
| `-n`, `--dry-run` | Do everything except delete. Identical to `scan` |
| `-y`, `--yes` | Do not ask for confirmation |
| `--non-interactive` | Never prompt, and proceed with the rules your configuration selects. Safety checks and the high-impact flag still apply |

```
sweepito clean [PATH] [selection options] [-n] [-y] [--non-interactive] [--json] [-q]
```

**Interactive (default).** With a terminal attached, `clean` shows the plan and asks:

```
$ sweepito clean
Project: /home/dev/demo   profiles: common, node, python, rust
                   Cleanup candidates
┌────────────────┬──────────────────┬──────┬──────┐
│ Rule           │ Path             │ Size │ Risk │
├────────────────┼──────────────────┼──────┼──────┤
│ python.pytest  │ .pytest_cache/   │  2 B │ safe │
│ python.pycache │ src/__pycache__/ │  9 B │ safe │
└────────────────┴──────────────────┴──────┴──────┘
Delete 2 item(s), 11 B? [y/N] y
Removed 2 item(s), 11 B freed.
```

Anything other than `y` or `yes` aborts with `Aborted. Nothing deleted.` and exit code 0.

**Skip the prompt:**

```
$ sweepito clean --risk configurable --yes
Removed 5 item(s), 24.4 KB freed.
```

**Without a terminal.** In scripts or CI, `clean` refuses to guess:

```
$ sweepito clean < /dev/null
sweepito: error: Confirmation required but no terminal is attached. Pass --yes or --non-interactive.
```

This exits with code **4** and deletes nothing. The same refusal happens if a terminal is
attached but no input arrives (end of input at the prompt). Pass `--yes` to confirm explicitly,
or `--non-interactive` for hooks and automation (it never prompts and acts on the rules
selected by your configuration).

**Dry run**, handy for CI previews or a final check before an unattended run:

```bash
sweepito clean --dry-run --risk configurable
```

**High-impact rules are opt-in.** They never run by default and never as part of `--risk
configurable`. Choose them explicitly, either one rule at a time or all at once:

```bash
sweepito clean --enable node.modules          # just node_modules/
sweepito clean --risk high-impact             # every high-impact rule
```

The plan is shown before anything is deleted, and without `--yes` you are asked to confirm.

**Nothing to do.** Prints `Nothing to clean.` and exits 0. With `--quiet` it prints nothing at
all, which is why hooks stay silent.

**Failures.** Locked or protected files are reported in red and never forced. The remaining
items are still processed, and the exit code is **1**:

```
failed: build/locked.dll: [WinError 5] Access is denied
```

**JSON.** `--json` replaces the formatted output with the plan plus the result. Note `removed`,
`failed` and `freed_bytes`:

```json
{
  "root": "/home/dev/demo",
  "profiles": ["common", "python", "rust"],
  "candidates": [
    {"rule": "python.pycache", "profile": "python", "risk": "safe",
     "path": "src/__pycache__", "is_dir": true, "size": 2}
  ],
  "skipped": [],
  "total_bytes": 2,
  "dry_run": false,
  "removed": [
    {"rule": "python.pycache", "profile": "python", "risk": "safe",
     "path": "src/__pycache__", "is_dir": true, "size": 2}
  ],
  "failed": [],
  "freed_bytes": 2
}
```

Tracked state is re-read immediately before deleting, so a file staged between planning and
deleting is still protected.

---

## `check`

Same output as `scan`, but exits **1** when candidates exist. Use it to fail a script or CI job
when a tree is not clean. It never deletes.

```
sweepito check [PATH] [selection options] [--json] [-q] [-v]
```

```
$ sweepito check --quiet
sweepito: 2 cleanup candidate(s), 11 B reclaimable (run 'sweepito scan').
$ echo $?
1

$ sweepito clean --yes --quiet
$ sweepito check
Project: /home/dev/demo   profiles: common, node, python, rust
Nothing to clean.
$ echo $?
0
```

---

## `report`

Summarise reclaimable space by profile, rule and risk. Unlike `scan`, it considers **every** rule
at **every** risk level, so it answers "how much space could I get back if I enabled everything?".
It never deletes, and ignores the risk ceiling. `--exclude` and `--disable` are still honoured.

```
sweepito report [PATH] [selection options] [--json]
```

```
$ sweepito report
Project: /home/dev/demo
By profile
┌─────────┬───────┬─────────┐
│ Profile │ Items │    Size │
├─────────┼───────┼─────────┤
│ rust    │     1 │ 19.5 KB │
│ node    │     2 │     4 B │
│ python  │     2 │     4 B │
└─────────┴───────┴─────────┘
By rule
┌────────────────┬───────┬──────────────┬─────────┐
│ Rule           │ Items │ Risk         │    Size │
├────────────────┼───────┼──────────────┼─────────┤
│ rust.target    │     1 │ configurable │ 19.5 KB │
│ node.next      │     1 │ configurable │     2 B │
│ python.pytest  │     1 │ safe         │     2 B │
│ node.modules   │     1 │ high-impact  │     2 B │
│ python.pycache │     1 │ safe         │     2 B │
└────────────────┴───────┴──────────────┴─────────┘
By risk
┌──────────────┬───────┬─────────┐
│ Risk         │ Items │    Size │
├──────────────┼───────┼─────────┤
│ configurable │     2 │ 19.5 KB │
│ safe         │     2 │     4 B │
│ high-impact  │     1 │     2 B │
└──────────────┴───────┴─────────┘
Total reclaimable if everything were enabled: 19.5 KB
```

Groups are sorted by size. `--json` prints `root`, `total_bytes`, and the `profile`, `rule` and
`risk` groups, each mapping a key to `{"count": n, "bytes": n}`. Entries in the `rule` group also
carry the rule's `risk`.

Use `report` to decide what to put in `enable` in your config, then `scan` with that config to
confirm.

---

## `rules`

List profiles and rules, or explain one rule. Custom rules from the project's config are
included.

```
sweepito rules [PATH] [-p PROFILE]... [--risk LEVEL] [--explain RULE] [--json] [--config FILE]
```

| Option | Meaning |
|---|---|
| `-p`, `--profile NAME` | Only these profiles. Repeatable |
| `--risk LEVEL` | Only rules at exactly this level (not "up to"). `--risk custom` lists just your own rules |
| `--explain RULE` | Describe one rule in full |

```
$ sweepito rules -p rust
                           Sweepito rules
┌─────────┬────────────────┬──────────────┬─────────┬─────────────────────────┐
│ Profile │ Rule           │ Risk         │ Default │ Description             │
├─────────┼────────────────┼──────────────┼─────────┼─────────────────────────┤
│ rust    │ rust.target    │ configurable │ opt-in  │ Cargo build output      │
│         │                │              │         │ (slow to rebuild)       │
│         │ rust.profiling │ configurable │ opt-in  │ Profiling output        │
└─────────┴────────────────┴──────────────┴─────────┴─────────────────────────┘
```

The `Default` column is `on` for rules that run by default (`safe` and `custom`) and `opt-in` for
the rest.
Profiles are separated by a rule, and the profile name is shown once per group:

```
$ sweepito rules -p node -p python --risk high-impact
┌─────────┬──────────────┬─────────────┬─────────┬────────────────────────────┐
│ Profile │ Rule         │ Risk        │ Default │ Description                │
├─────────┼──────────────┼─────────────┼─────────┼────────────────────────────┤
│ node    │ node.modules │ high-impact │ opt-in  │ Installed dependencies     │
│         │              │             │         │ (requires reinstall)       │
├─────────┼──────────────┼─────────────┼─────────┼────────────────────────────┤
│ python  │ python.venv  │ high-impact │ opt-in  │ Virtual environments       │
└─────────┴──────────────┴─────────────┴─────────┴────────────────────────────┘
```

**Explain a rule** to see exactly what it targets and requires:

```
$ sweepito rules --explain node.next
┌────────────────────────────── Rule node.next ───────────────────────────────┐
│ Profile          node                                                       │
│ Risk             configurable                                               │
│ Paths            /.next/                                                    │
│ Requires         next.config.*                                              │
│ Allow untracked  no                                                         │
│ Description      Next.js build output                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

A leading `/` in `Paths` anchors the pattern to the directory containing the `Requires` marker;
other patterns match at any depth below it. `--json` returns the rule's fields, or a
`{"rules": [...]}` list when listing. An unknown ID is exit 2.

---

## `profiles`

List every profile (technology), or describe one. Custom profiles from the project's config are
included. It is the profile-level counterpart of [`rules`](#rules).

```
sweepito profiles [PATH] [--explain PROFILE] [--json] [--config FILE]
```

| Option | Meaning |
|---|---|
| `--explain PROFILE` | Describe one profile and list its rules |

```
$ sweepito profiles
                                  Sweepito profiles
┌─────────┬──────────────────────────┬─────────────────────┬───────┬──────┬──────────────┬─────────────┐
│ Profile │ Description              │ Detected by         │ Rules │ Safe │ Configurable │ High-impact │
├─────────┼──────────────────────────┼─────────────────────┼───────┼──────┼──────────────┼─────────────┤
│ common  │ OS and editor artifacts  │ always active       │     5 │    2 │            3 │           0 │
│         │ that apply to any        │                     │       │      │              │             │
│         │ project                  │                     │       │      │              │             │
│ dart    │ Dart and Flutter         │ pubspec.yaml        │     3 │    0 │            3 │           0 │
│ go      │ Go modules and build     │ go.mod, go.work     │     3 │    1 │            1 │           1 │
│         │ tools                    │                     │       │      │              │             │
│ rust    │ Rust and Cargo           │ Cargo.toml          │     2 │    0 │            2 │           0 │
│ ...     │                          │                     │       │      │              │             │
└─────────┴──────────────────────────┴─────────────────────┴───────┴──────┴──────────────┴─────────────┘
```

`Detected by` lists the marker files that activate a profile under auto-detection; a profile
with none, such as `common`, is always active. The count columns are the profile's rules by risk
level (see [Concepts](#concepts)). The listing comes from the built-in profiles plus your
config, not from scanning the project, so it is the same in every directory unless a config adds
profiles. To see which profiles a project activates, use `sweepito scan` (the header line) or
`sweepito doctor`.

**Explain a profile** to see its details and rules:

```
$ sweepito profiles --explain rust
┌─────────────────────────────── Profile rust ────────────────────────────────┐
│ Description  Rust and Cargo                                                 │
│ Detected by  Cargo.toml                                                     │
│ Rules        2 (0 safe, 2 configurable, 0 high-impact)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                               Sweepito rules
┌─────────┬────────────────┬──────────────┬─────────┬─────────────────────────┐
│ Profile │ Rule           │ Risk         │ Default │ Description             │
├─────────┼────────────────┼──────────────┼─────────┼─────────────────────────┤
│ rust    │ rust.target    │ configurable │ opt-in  │ Cargo build output      │
│         │                │              │         │ (slow to rebuild)       │
│         │ rust.profiling │ configurable │ opt-in  │ Profiling output        │
└─────────┴────────────────┴──────────────┴─────────┴─────────────────────────┘
```

An unknown name is exit 2 (`sweepito: error: Unknown profile 'nope'.`).

**JSON.** `--json` prints `{"profiles": [...]}` with, for each profile, `id`, `description`,
`markers`, `always_active`, `rules` (a count) and the counts `safe`, `configurable` and
`high_impact`. With `--explain`, it prints that profile with a `rules` list instead (each rule
has `id`, `risk`, `paths`, `requires` and `description`).

---

## `config`

Inspect or validate the configuration that applies to a project.

```
sweepito config show     [PATH] [--config FILE] [--json]
sweepito config validate [PATH] [--config FILE] [--json]
```

### `config show`

Shows the effective settings (after merging the file with defaults), which file was used, and
the custom rules it defines:

```
$ sweepito config show
┌────────────────────────── Sweepito configuration ───────────────────────────┐
│ Config file     none (built-in defaults)                                    │
│ Profiles        auto                                                        │
│ Risk ceiling    safe                                                        │
│ Enabled rules   -                                                           │
│ Disabled rules  -                                                           │
│ Excluded paths  -                                                           │
│ Custom rules    -                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

With a file, `Config file` shows its path and the lists are filled in. `--json` prints the same
data as JSON for scripts:

```json
{
  "config_file": "/home/dev/demo/sweepito.toml",
  "settings": {"profiles": ["auto"], "risk": "configurable", "enable": ["rust.target"], ...},
  "custom_rules": ["custom.test-output"]
}
```

`config show` reflects the file only. Command-line overrides such as `--risk` apply to the
command you run, not here.

### `config validate`

Parses and checks the file. Prints `Configuration OK.` (green) and exits 0, or reports the
first problem and exits **2**. Use it in CI or a pre-commit hook:

```
$ sweepito config validate
sweepito: error: Unknown key(s) in [clean]: bogus.
$ echo $?
2
```

Things it catches: invalid TOML, unknown sections or keys, bad risk values, duplicate or
malformed rule IDs, unsafe paths (`../etc/`, `C:/...`, `~`, backslashes, negations), `exec`
rules (not supported yet) and rule IDs that clash with built-in ones. Unknown rule or profile
names in `enable`, `disable` and `-p` are caught when you run a command, not here.

---

## `init`

Write a starter `sweepito.toml` in the project root.

```
sweepito init [PATH] [--force]
```

```
$ sweepito init
Wrote /home/dev/demo/sweepito.toml
$ head -5 sweepito.toml
# Detected profiles: common, node, python, rust
# Sweepito configuration. See 'sweepito rules' for rule IDs.

[defaults]
profiles = ["auto"]   # or an explicit list, e.g. ["python", "node"]
```

The file lists the detected profiles in a comment and contains commented examples of `enable`,
`exclude`, `[hook]` and a custom rule. If a `sweepito.toml` already exists, `init` refuses
(exit 4) unless you pass `--force`:

```
$ sweepito init
sweepito: error: /home/dev/demo/sweepito.toml already exists. Use --force to overwrite.
```

---

## `hook`

Install, remove or inspect a native Git hook. This is for people who do not use the
[`pre-commit`](https://pre-commit.com) framework (which has its own setup, see the README).

```
sweepito hook install   [PATH] [--stage STAGE]
sweepito hook uninstall [PATH] [--stage STAGE]
sweepito hook status    [PATH] [--json]
```

| Option | Meaning |
|---|---|
| `--stage post-commit` | **Default.** Clean after each commit |
| `--stage pre-commit` | Report only, before each commit. It never blocks the commit |

All three need a Git repository (otherwise exit 4). The hook location respects
`core.hooksPath`.

```
$ sweepito hook install
Installed post-commit hook: /home/dev/demo/.git/hooks/post-commit
$ sweepito hook status
      Sweepito hooks
┌─────────────┬───────────────┐
│ Stage       │ State         │
├─────────────┼───────────────┤
│ post-commit │ installed     │
│ pre-commit  │ not installed │
└─────────────┴───────────────┘
$ sweepito hook uninstall
Removed post-commit hook.
$ sweepito hook uninstall
No post-commit hook installed.
```

**What gets written.** A delimited block, appended to the existing hook if there is one:

```sh
#!/bin/sh

# >>> sweepito >>>
if command -v sweepito >/dev/null 2>&1; then
  sweepito clean --hook --non-interactive --quiet || echo "sweepito: post-commit hook failed" >&2
fi
# <<< sweepito <<<
```

- Installing twice does not duplicate the block.
- Anything already in the hook is preserved. `uninstall` removes only the Sweepito block, and
  deletes the file only if Sweepito created it and nothing else is in it.
- If `sweepito` is not on `PATH`, the hook does nothing and cannot break commits.
- `--hook` makes the run apply the `[hook]` section of your config (a lower `risk`, `quiet`).
- A post-commit hook cannot fail a commit. If cleanup fails it prints one line to stderr.

`hook status --json` prints `{"post-commit": false, "pre-commit": false}`.

---

## `doctor`

Diagnose the environment and show what Sweepito will use. Handy when filing a bug report.

```
sweepito doctor [PATH] [--config FILE] [--json] [--no-color]
```

A passing check shows a green `OK`. A failing check shows a red `FAILED` if it is required, or
`MISSING` if it is optional.

```
$ sweepito doctor
                          Sweepito doctor
┌──────────────────┬─────────┬─────────────────────────────────────┐
│ Check            │ Result  │ Details                             │
├──────────────────┼─────────┼─────────────────────────────────────┤
│ Sweepito         │ OK      │ 0.1.0                               │
│ Python           │ OK      │ 3.11.9 (requires 3.11+)             │
│ pathspec         │ OK      │ 1.1.1                               │
│ rich             │ OK      │ 15.0.0                              │
│ Git              │ OK      │ git version 2.45.0                  │
│ Project root     │ OK      │ /home/dev/demo                      │
│ Configuration    │ OK      │ none (built-in defaults)            │
│ Risk ceiling     │ OK      │ safe                                │
│ Git repository   │ OK      │ yes                                 │
│ Profiles         │ OK      │ common, node, python, rust          │
│ post-commit hook │ MISSING │ not installed                       │
│ pre-commit hook  │ MISSING │ not installed                       │
└──────────────────┴─────────┴─────────────────────────────────────┘
```

| Check | Required | Meaning |
|---|---|---|
| Sweepito | No | Installed version |
| Python | Yes | Version, and that it is 3.11 or newer |
| pathspec, rich | Yes | Dependencies are installed |
| Git | Yes | The `git` executable is on `PATH` |
| Project root | Yes | The directory resolved from `PATH` or the current directory |
| Configuration | Yes | The config file in use (or built-in defaults), and that it parses |
| Risk ceiling | No | The highest risk level selected by default |
| Git repository | No | Whether the root is in a Git repository (cleaning is refused if not) |
| Profiles | No | Profiles that auto-detection activates for this project |
| post-commit / pre-commit hook | No | Whether the native Sweepito hook block is installed |

An invalid configuration does not crash `doctor`. It shows up as a failed `Configuration` row so
you can see the error:

```
│ Configuration │ FAILED │ Unknown key(s) in [clean]: bogus.                │
```

The exit code is 0 when every **required** check passes (missing hooks never fail it) and 1
otherwise. `--json` returns `{"healthy": bool, "checks": [{"name", "ok", "detail",
"required"}, ...]}`.

---

## Output and colour

Every command renders through [Rich](https://github.com/Textualize/rich): tables for lists,
panels for single items, and colour for status (green for success and `safe`, yellow for
`configurable` and warnings, red for `high-impact`, failures and errors).

- Errors and interruptions go to **stderr**; results go to **stdout**.
- `--no-color` removes colour. Rich also disables colour automatically when output is not a
  terminal and honours the `NO_COLOR` environment variable.
- `--json` bypasses Rich entirely and prints plain JSON, so it is always safe to pipe.
- Table borders use box-drawing characters in a terminal that supports them, and ASCII
  otherwise.

## Exit codes

| Code | Meaning | Examples |
|---|---|---|
| 0 | Success, including "nothing to clean" and declining the prompt | |
| 1 | Some items failed or were skipped; `check` found candidates; a required `doctor` check failed | Access denied on a locked file |
| 2 | Usage or configuration error | Unknown rule or profile, invalid config, missing `--config` file |
| 3 | Unexpected error | A bug; please report it |
| 4 | Safety refusal | Not a Git repo, no consent in a non-interactive `clean`, `init` over an existing file |
| 130 | Interrupted | Ctrl+C |

Errors are printed to stderr as `sweepito: error: <message>`.

## JSON output

`scan`, `clean --dry-run` and `check` print:

| Field | Meaning |
|---|---|
| `root` | Absolute project root |
| `profiles` | Active profile IDs |
| `candidates[]` | `rule`, `profile`, `risk`, `path` (posix, relative to root), `is_dir`, `size` (bytes) |
| `skipped[]` | `path`, `rule`, `reason` |
| `total_bytes` | Sum of candidate sizes |
| `dry_run` | `true` for scan, check and `clean --dry-run` |

`clean` adds `removed[]` (same shape as `candidates`), `failed[]` (`path`, `error`) and
`freed_bytes`. `--json` always writes the document to stdout and diagnostics to stderr, so it is
safe to pipe:

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

# Fail CI if caches were committed to the working tree by a build step
sweepito check --quiet

# Reset a node project completely (dependencies too)
sweepito clean -p node --enable node.modules --yes

# Preview with machine-readable output for a dashboard
sweepito scan --risk configurable --json > sweepito-report.json

# Validate config in a pre-commit hook
sweepito config validate

# Use a shared config for several repositories
sweepito clean --config ~/.config/sweepito/team.toml --yes
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `... is not inside a Git repository` (exit 4) | Run it inside a repo, or pass `--no-git-check` knowing nothing can be verified as ignored |
| A folder you expected is not listed | It may not be git-ignored. Add it to `.gitignore`, or define a custom rule with `allow_untracked = true`. Check `sweepito scan -v` for a skip reason and `sweepito rules --explain RULE` for its marker requirement |
| `Confirmation required but no terminal is attached` | Add `--yes` (explicit) or `--non-interactive` (automation) |
| `Unknown rule ID(s)` | Run `sweepito rules` for the list. IDs are case-sensitive and contain a dot |
| Rule seems to match nothing | Its marker file must exist beside (or above) the folder. `build/` needs e.g. `CMakeLists.txt`, `pom.xml`, `build.gradle` depending on the rule |
| Hook ran but nothing happened | Hooks are quiet by design. Run `sweepito scan -v` by hand, and `sweepito doctor` to check the hook is installed and `sweepito` is on `PATH` |
