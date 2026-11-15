# VS Code extension

The extension in `extensions/vscode/` is a native JavaScript port of the Sweepito scan and
clean pipeline. It does not call Python or the `sweepito` command line tool.

## Layout

```text
extensions/vscode/
  src/extension.js      activation, commands, tree view, status bar (the only vscode imports)
  src/tree-model.js     builds the profile > rule > path tree as plain data
  src/core/             no vscode imports; unit tested
    models.js           risk levels, format_size
    registry.js         bundled profiles plus custom profiles and rules
    config.js           config discovery, validation and merging
    api.js              prepare/scan/report: config + registry + plan
    catalog.js          Markdown for the rules and profiles lists and explain pages
    markdown.js         table and escaping helpers
    init.js             create, validate and show the configuration (`init`, `config`)
    precommit.js        detects the pre-commit framework (config, generated hooks, shadowed blocks)
    hooks.js            hook install/uninstall/status; shares the CLI's block markers
    hookRun.js          what the bundled hook script does (scan/clean at the [hook] risk)
    doctor.js           the checks behind Sweepito: Doctor
    json.js             CLI-shaped JSON for scan, report, doctor, rules, profiles, config
    terminal.js         ANSI-coloured tables for the Sweepito terminal (colour switchable)
    text.js             plain-text summaries for the output channel
    report.js           totals by profile, rule and risk; Markdown rendering
    git.js              wrappers around the git binary
    planner.js          detect, match, gate: port of planner.py
    executor.js         deletes candidates: port of executor.py
    profiles.json       generated, not committed
  scripts/build.mjs     profiles.json, config template and LICENSE from the repository
  src/hook-cli.js       entry point of dist/sweepito-hook.js
  esbuild.mjs           bundles dist/extension.js and dist/sweepito-hook.js
```

## Profiles stay in one place

`src/sweepito/profiles/*.toml` remains the only source of truth. `npm run build` and
`npm test` first run `scripts/build.mjs`, which converts the TOML files into
`src/core/profiles.json`. Add or change a rule in the TOML and rebuild; nothing else needs
to change.

## Behaviour matches the Python tool

The core follows the same pipeline as [architecture.md](architecture.md): inventory with
`git ls-files`, marker detection, rule matching, then the safety gates (inside `.git`,
excluded, escapes the root, tracked, not ignored by git) and parent collapsing. Tracked state
is re-read right before deleting. Links are removed as links and never traversed.

Differences from the CLI:

- `sweepito.noGitCheck` is the `--no-git-check` equivalent: outside a Git repository it
  walks the folder itself and skips the tracked and ignored gates. It is machine-scoped,
  ignored in untrusted workspaces, and cleaning always asks for an extra confirmation.
  Inside a repository the git gates always run, as in the CLI.
- Configuration comes from VS Code settings and from `sweepito.toml`, `.sweepito.toml` or
  `[tool.sweepito]` in `pyproject.toml`, found from the workspace up to the Git root
  (`core/config.js`). Custom rules (`sweepito.customRules`), custom profiles
  (`sweepito.customProfiles`), `allow_untracked` and the CLI's pattern validation are all
  ported. The file's `[hook]` table is validated but unused, and `exec` rules are rejected as
  in the CLI.
- A VS Code value for `risk` or `profiles` wins over the file only when the user set it;
  `enable`, `disable`, `exclude`, rules and profiles from both sources are combined.
- `risk` accepts `custom`, which selects only user rules.
- `sweepito.configFile` and `sweepito.noGitCheck` are machine-scoped and ignored in untrusted
  workspaces.
- `Sweepito: Report` is the `report` command: it plans at `high-impact` (honouring enable,
  disable and exclude) and opens the totals as Markdown. There is no `--json` form.
- `List Rules` (with profile and risk filters), `List Profiles`, `Explain Rule` and
  `Explain Profile` are the `rules` and `profiles` commands, shown as Markdown. There is no
  `--json` form, and the extension has no `--hook` option.
- `Sweepito: Doctor` replaces the Python-specific checks (Python version, `pathspec`, `rich`)
  with the extension version and Node, and adds a "Hook runtime" check.
- Hooks use the same `# >>> sweepito >>>` markers as the CLI, so each tool detects, replaces and
  removes the other's block. The extension's block runs `sweepito` if on `PATH`, else
  `node "$(dirname "$0")/sweepito-hook.js"`, a copy of `dist/sweepito-hook.js` placed next to
  the hook (removed with the last Sweepito block). It does not pin a Python interpreter; a pin
  written by the CLI is still checked by Doctor. Installing, uninstalling and the hook
  settings are ignored in untrusted workspaces.
- `Create Config File` is `init`: it writes `sweepito.toml` at the Git root with the detected
  profiles as a header, using the CLI's own template (copied into `src/core/` at build time).
  `Show Effective Configuration` and `Validate Configuration` are `config` and `config validate`.
  Overwriting an existing file needs confirmation, and creating is blocked in untrusted
  workspaces.
- The pre-commit framework hooks (`.pre-commit-hooks.yaml`, `language: python`) are consumed by
  other projects' configs, so there is nothing to port. The extension only detects the
  framework: a hook file containing `File generated by pre-commit` ends with `exec`, so a
  Sweepito block added to it never runs. Install refuses in that case, and Doctor and hook
  status report it. Editing `.pre-commit-config.yaml` and a `language: node` entry are not
  implemented.
- Multi-root workspaces: every folder is scanned in parallel and keeps its own state (plan,
  error, rule descriptions). The tree adds a folder level only when there are several folders,
  and a folder that fails (for example, not a Git repository) shows an error node while the rest
  work. Settings come from `getConfiguration("sweepito", folderUri)`. Candidates carry the
  folder they came from, so cleaning a mixed selection deletes each from its own folder.
  Commands that act on one folder (report, doctor, hooks, config, rules, JSON) ask which, if
  there is more than one; there is no "all folders" form for them.
- `Sweepito: Check` is `check`: it scans, reports whether anything is left, and offers to clean.
  There is no exit code; the status bar turns amber while items remain after a check.
- `Open Result as JSON` / `Copy Result as JSON` replace `--json` for scan, report, doctor,
  rules, profiles, config and hook status, with the CLI's keys.
- The Sweepito terminal (`Show Terminal`) stands in for rich output: an extension-owned
  pseudoterminal that prints tables with ANSI colour. `sweepito.terminal.color` is `--no-color`
  (the text is identical without escape codes). It receives scan, clean, report, doctor and
  rules results only while it is open, and never opens by itself. Check and Explain are not
  mirrored there.
- `Open/Copy Result as JSON` includes `clean`: the plan and outcome of the last clean in the
  chosen folder this session, in the shape of `clean --json`. It is kept in memory only and does
  not run a clean.
- The output channel replaces terminal output: plain text, no colour. `sweepito.quiet` logs only
  failures. Scans started automatically are not logged unless they fail.
- Glob matching uses the `ignore` package where Python uses `pathspec`.

## Development

```bash
cd extensions/vscode
npm install
npm test                 # unit tests (Vitest)
npm run build            # bundle to dist/
npm run test:integration # needs a display or xvfb; downloads VS Code the first time
npm run package          # build the .vsix
```

Press F5 in VS Code on the `extensions/vscode` folder to launch an Extension Development Host.
