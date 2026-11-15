# Sweepito for VS Code: guide

The full guide to the Sweepito extension. The short version is in the
[extension README](../../extensions/vscode/README.md).

Free up disk space by cleaning caches and build output that your projects can regenerate,
without leaving the editor. Sweepito only ever removes files that Git ignores, so your source
code and anything tracked by Git is never touched.

It runs natively inside VS Code. You do not need Python or the Sweepito command line tool.
You only need Git.

## What you get

- **Cleanup candidates view.** Open the Sweepito icon in the activity bar to see what can be
  cleaned, grouped by technology, then by rule, with the size of each item.
- **Status bar.** Shows how much space can be reclaimed. Click it to scan again.
- **Command Palette.** Run **Sweepito: Scan**, **Sweepito: Clean**, **Sweepito: Report** or
  **Sweepito: Choose Risk Level for This Session**.
- **Browse rules and profiles.** **Sweepito: List Rules** and **Sweepito: List Profiles** show
  every rule or technology Sweepito knows, including your own. **Sweepito: Explain Rule** and
  **Sweepito: Explain Profile** show one in detail: its paths, the files that switch it on, and
  its risk. You can also right-click a profile or rule in the Sweepito view and choose Explain.
- **Config file.** **Sweepito: Create Config File** writes a starter `sweepito.toml` for your
  project. **Sweepito: Show Effective Configuration** shows what is in force, and
  **Sweepito: Validate Configuration** checks the file for mistakes.
- **Doctor.** **Sweepito: Doctor** checks Git, your configuration, the detected technologies
  and any installed hook, and tells you what is wrong.
- **Git hook.** **Sweepito: Install Git Hook** sets up a hook so cleaning (`post-commit`) or a
  report (`pre-commit`) runs on every commit. **Uninstall Git Hook** and **Show Git Hook Status**
  manage it. Existing hook content is kept, and you confirm before anything is installed.
- **Check.** **Sweepito: Check** scans and tells you whether anything is left to clean. If so,
  it offers to clean or show the list, and the status bar turns amber until it is gone.
- **JSON.** **Sweepito: Open Result as JSON** and **Copy Result as JSON** give you the scan,
  report, doctor, rules, profiles, configuration, hook status or your last clean as JSON, in the same shape as
  the command line tool's `--json`.
- **Output panel.** Scans, cleans, reports and checks also write a plain-text summary to the
  **Sweepito** output panel (**Sweepito: Show Output**). Turn on `sweepito.quiet` to log only
  failures.
- **Sweepito terminal.** **Sweepito: Show Terminal** opens a terminal tab (it has no shell) that
  prints scan, clean, report, doctor and rules results as coloured tables, like the command line
  tool. Turn `sweepito.terminal.color` off for plain text. Results appear once the terminal is
  open.
- **Several folders.** In a multi-root workspace every folder is scanned, the view groups items by
  folder, and the status bar adds them up. Settings are read per folder. Commands that act on one
  folder, such as Report, Doctor or the Git hook, ask which one.
- **Report.** **Sweepito: Report** shows how much space could be reclaimed by technology, by
  rule and by risk level, across every risk level, without deleting anything.
- **Clean as much or as little as you like.** Use the trash icon on the whole list, a
  technology, a rule or a single folder. Sweepito asks you to confirm first.

## Getting started

1. Open a folder that is a Git repository.
2. Open the Sweepito view. The workspace is scanned for you.
3. Review the list, then clean what you want.

By default only the safest items are listed. Choose a higher risk level to see larger
artifacts, such as build output that takes time to rebuild.

## Settings

| Setting | Default | What it does |
|---|---|---|
| `sweepito.risk` | `safe` | Highest risk level to scan and clean: `safe`, `configurable` or `high-impact`. Choose `custom` to run only your own rules. |
| `sweepito.profiles` | `["auto"]` | Technologies to scan. `auto` detects them from your files; list IDs such as `node` to force them. |
| `sweepito.enableRules` | `[]` | Rule IDs to turn on regardless of risk level. |
| `sweepito.disableRules` | `[]` | Rule IDs to turn off. |
| `sweepito.exclude` | `[]` | Gitignore-style patterns that are never touched. |
| `sweepito.customRules` | `[]` | Your own cleanup rules (see below). They always run and appear under the `custom` risk level. |
| `sweepito.customProfiles` | `{}` | Your own technologies, or extra marker files for built-in ones. |
| `sweepito.configFile` | `""` | Use this config file instead of searching for one. |
| `sweepito.noGitCheck` | `false` | High impact: also scan folders that are not Git repositories. Cleaning there always asks for an extra confirmation. |
| `sweepito.confirmBeforeClean` | `true` | Ask before deleting anything. |
| `sweepito.quiet` | `false` | Write only failures to the Sweepito output panel. |
| `sweepito.terminal.color` | `true` | Use colour in the Sweepito terminal. Off is the same as the command line tool's `--no-color`. |
| `sweepito.autoScan` | `true` | Scan when the workspace opens. |
| `sweepito.statusBar.enabled` | `true` | Show the reclaimable size in the status bar. |

## Your own rules

Add rules in `settings.json`:

```json
"sweepito.customRules": [
  { "id": "team.out", "paths": ["out/"], "description": "Build output" }
],
"sweepito.customProfiles": {
  "myteam": { "markers": ["Teamfile"], "description": "Our build tool" }
}
```

A rule needs an `id` and `paths`. It can also set `requires`, `requires_all`, `profile` and
`description`. Rules and profiles from a `sweepito.toml` (or `[tool.sweepito]` in
`pyproject.toml`) are read too, so a project can share them with the command line tool.
Settings you choose in VS Code win over the file for `risk` and `profiles`; everything else is
combined. If a rule or setting is invalid, the status bar shows a warning with the reason.

A rule with `allow_untracked` can also match files that Git does not ignore. Tracked files are
still never removed. Use it with care.

## Git hook

The hook runs the `sweepito` command if it is installed. If not, it runs a small script that
ships with this extension, which needs `node` on your `PATH`. With neither, the hook does
nothing and Doctor says so. A hook installed by the Sweepito command line tool is recognised and
can be removed from VS Code, and the other way round. Hook settings (`risk`, `quiet`) come from
the `[hook]` section of `sweepito.toml`.

### Using pre-commit

If your project uses the [pre-commit](https://pre-commit.com) framework, add Sweepito to
`.pre-commit-config.yaml` as described in the Sweepito README rather than installing the hook
from VS Code. The framework writes its own hook script, which ends by handing over to
`pre-commit`, so a hook added from VS Code would never run. Sweepito: Install Git Hook explains
this and stops, Doctor reports a block that cannot run, and Show Git Hook Status says when
pre-commit manages a hook.

## Safety

- Only git-ignored files are removed. Tracked files and anything inside `.git` are skipped.
- Symbolic links and junctions are removed as links and never followed.
- In an untrusted workspace Sweepito can scan but not clean.
- Sweepito sends nothing over the network.

## Notes

- Git must be installed and available on your `PATH`. Folders that are not Git repositories
  are only scanned when `sweepito.noGitCheck` is on.
