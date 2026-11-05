# VS Code extension: implementation analysis (issue #15)

Status: proposal. Nothing is implemented yet.

## Core idea

The extension is a thin TypeScript UI over the Python CLI. It spawns `sweepito ... --json`
(no shell, args as an array), parses stdout, and never deletes anything itself. No Python
runs inside VS Code, and there is no language server.

## Findings from the current CLI

| Need | CLI today | Gap |
|---|---|---|
| Scan tree | `scan --json` gives `candidates[]` with `rule, profile, risk, path, is_dir, size`, plus `skipped[]` and `total_bytes` | None. Per-item size already exists, which answers the open point in the issue |
| Rule list for settings and toggles | `rules --json` | None |
| Doctor | `doctor --json` gives `{healthy, checks[]}` | None |
| Hooks | `hook status --json`, `hook install/uninstall --stage` | None. Install and uninstall print text only, so rely on the exit code |
| Version check | `--version` prints `sweepito 0.1.0` as text | **Gap:** no JSON version. Either parse the text (fragile) or use `doctor --json` (its "Sweepito" check carries the version) |
| Clean | `clean --yes --json` returns `removed[]`, `failed[]`, `freed_bytes` | **Gap:** no way to clean individual paths, only by rule, profile, risk and `-x` excludes |
| Exit codes | 0 ok, 1 partial or failed, 2 usage, 3 bug, 4 safety refusal | Usable as is |

### The one real design gap: "clean selected items"

`clean` selects by rule, not by path. Options:

1. **Add `--only PATH` (repeatable) to `clean`/`scan`** (recommended). It restricts candidates
   to the given paths, but only after the normal safety pipeline, so it can never widen the
   selection. This is a small, well-tested CLI change and keeps "every removal goes through
   `sweepito clean`".
2. Emulate it with `--enable <rule>` plus `-x` for every unselected path. This needs no CLI
   change, but it is fragile and the command line can get long.
3. Limit v1 to rule-level, profile-level and "all safe" cleaning. Per-item selection comes later.

Recommendation: ship 3 first if you want it fast, but plan 1. It is the only CLI change
needed. A `schema_version` field in the JSON output is a worthwhile, cheap addition too, so
the extension can detect incompatible output.

Safety flow in the extension: run `clean --dry-run --json` with the exact flags, show the
list in a modal, then run `clean --yes --json` with those same flags. Re-scan afterwards. The
modal always lists what the dry run returned. Risk levels `configurable` and `high-impact` are
off by default and need a separate explicit opt-in (a checkbox or QuickPick step) that maps to
`--risk`/`--enable`.

## Repo layout (same repo, recommended)

The CLI and extension share a JSON contract that changes together, so one repo with one CI
makes breakage visible immediately.

```
extensions/vscode/
  package.json          # contributes: views, commands, configuration, capabilities
  tsconfig.json
  esbuild.mjs           # bundle to dist/extension.js
  src/
    extension.ts        # activate(): register views, commands, status bar
    cli/locate.ts       # settings path -> PATH -> active Python interpreter
    cli/run.ts          # execFile wrapper, timeout, cancellation, JSON parse, exit-code map
    cli/types.ts        # typed JSON schemas (scan, clean, rules, doctor, hook)
    views/scanTree.ts   # TreeDataProvider: workspace folder > profile > rule > path
    commands/*.ts       # scan, clean, doctor, hook install/uninstall
    statusBar.ts
  test/
    fixtures/repo/      # created at test time with git init, a .gitignore and a few caches
    suite/*.test.ts
  README.md
```

## Behaviours

- **CLI discovery**, in the order the issue gives:
  1. `sweepito.executablePath`.
  2. `sweepito` on `PATH`.
  3. The interpreter from the `ms-python.python` API, run as `python -m sweepito`
     (`__main__.py` already exists).

  Then run `doctor --json`, or `--version`, and compare with a minimum version constant. If
  nothing is found or it is too old, show a message with `pip install sweepito`,
  `pipx install sweepito` and a settings button. Standalone installers (#7) will be detected
  via `PATH` with no extra work.
- **Multi-root**: one scan per `workspaceFolders` entry, passing `PATH` explicitly. The tree's
  top level is the folder when there is more than one. Debounce re-scans on save or `.gitignore`
  change, and never scan automatically on large workspaces unless `sweepito.autoScan` is on.
- **Settings** (mirror the TOML): `executablePath`, `risk` (safe|configurable|high-impact),
  `enableRules[]`, `disableRules[]`, `exclude[]`, `configFile`, `autoScan`, `statusBar.enabled`.
  These are translated to CLI flags. The project's own `sweepito.toml` or `[tool.sweepito]`
  stays the source of truth, since the CLI merges both.
- **Untrusted workspaces**: `capabilities.untrustedWorkspaces: { supported: "limited" }`. In
  limited mode only Scan, Doctor and hook status work. Clean and hook install/uninstall are
  disabled. Also disable `executablePath` from workspace settings when untrusted
  (`restrictedConfigurations`), because a workspace-controlled executable path is arbitrary code
  execution.
- **Security**: use `execFile` only, never a shell. Pass paths as args and never interpolate
  them into strings. Treat CLI output as untrusted data. Cap output size.
- **Status bar**: `$(trash) 24.4 KB` from `total_bytes`, click runs Scan.

## Testing and CI

- **Unit** (Mocha, no VS Code): the CLI locator, flag builder, JSON parsing against recorded
  fixtures, and exit-code mapping. This is fast and runs on every PR.
- **Integration** (`@vscode/test-electron`): launch VS Code on a fixture repo and a real
  `uv run sweepito` installed in CI. Assert that the tree is populated, a clean after
  confirmation removes the ignored caches, and a tracked file is never touched. Run on
  ubuntu, plus windows and macos for path handling.
- **Contract test (Python side)**: add a test in `tests/` that snapshots the JSON keys that the
  extension depends on, so a CLI change that breaks the extension fails in the Python suite.
- **New workflow** `extension.yml`, path-filtered to `extensions/vscode/**` and `src/**`: lint,
  typecheck, test, `vsce package` and upload the `.vsix` as an artifact.
- **Release**: the existing `release.yml` is tag-driven (`v*.*.*`) and checks that versions
  match. Extend it: add the extension `package.json` version to the version check, build the
  `.vsix`, attach it to the GitHub release, and publish with `vsce publish` (secret `VSCE_PAT`)
  and `ovsx publish` (secret `OVSX_PAT`). Add the extension version to the same tag check so the
  two never drift. It could also be a separate `ext-v*` tag if you want independent cadences;
  I suggest lockstep versions at first, for simplicity.

## Phasing

1. **CLI prep** (Python, small): `--only PATH`, `schema_version` in JSON, doc updates in
   `docs/cli.md`, contract test. This is optional for v1 if you choose option 3 above.
2. **MVP extension**: locator, scan tree, Scan/Doctor/Hook commands, settings, untrusted mode.
3. **Clean flow**: dry-run modal, risk opt-in, rule-level and "all safe" clean, then
   per-item selection.
4. **Packaging and release**: CI, `.vsix`, Marketplace and Open VSX, README with install and
   usage, `docs/vscode.md`, and a link from the README.
5. **Polish**: status bar, multi-root tuning, icons, and a CHANGELOG entry.

## Open points for you

- Marketplace name and publisher ID (for example `coldsofttech.sweepito`). A publisher
  account and PATs for both registries are needed before the first release.
- Same repo (recommended) or separate repo.
- Whether to add `--only PATH` to the CLI for v1.
- Minimum supported VS Code version (suggest `^1.90`) and Node LTS for the build.
