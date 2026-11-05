# VS Code extension

The extension in [`extensions/vscode`](../extensions/vscode) is a thin front end for the
command line tool. It starts `sweepito ... --json`, parses the output and shows it in a tree.
It never deletes files itself: every removal is `sweepito clean --yes`, run only after the user
confirmed a `--dry-run` built from the same options. For installation and use, see the
[extension README](../extensions/vscode/README.md).

## How it talks to the CLI

| Feature | Command |
|---|---|
| Scan tree | `scan PATH [selection options] --json` |
| Confirmation | `clean PATH [same options] --dry-run --json` |
| Clean | `clean PATH [same options] --yes --json` (exit 0, or 1 when some items failed) |
| Rule list (for a rule-level clean) | `rules PATH --json` |
| Doctor | `doctor PATH --json` (exit 1 still prints the document) |
| Git hooks | `hook status\|install\|uninstall PATH [--stage S]`, `status` with `--json` |
| Create config | `init PATH` |
| Version | `--version` (`sweepito X.Y.Z`) |

A rule-level clean has no CLI equivalent, so the extension enables that rule and disables every
other one (`--disable` always wins). A profile-level clean uses `--profile`. Exit code 4 on a scan
means "not a Git repository".

**The JSON output is a contract.** [`tests/test_extension_contract.py`](../tests/test_extension_contract.py)
pins the fields the extension reads. If you change them, update
`extensions/vscode/src/cli/types.ts` in the same change.

## Layout

```
extensions/vscode/
  src/cli/      args, run (execFile, no shell), locate, version, types: no `vscode` import
  src/service.ts  typed wrapper around the CLI
  src/ui/       tree, confirmation dialogs, install help, settings
  src/extension.ts  commands, watchers, status bar
  test/         node:test unit tests and an integration test against the real CLI
```

Code under `src/cli` and `src/service.ts` does not import `vscode`, so it is tested in plain
Node.

## Develop

```bash
cd extensions/vscode
npm ci
npm run typecheck
SWEEPITO_BIN=$(pwd)/../../.venv/bin/sweepito npm test   # uv sync at the repo root first
npm run build && npm run package                          # produces sweepito-X.Y.Z.vsix
```

Press F5 in VS Code with `extensions/vscode` open (a launch configuration pointing at
`dist/extension.js` after `npm run build`) to try it in an Extension Development Host. Install a
built package with **Extensions: Install from VSIX**.

The integration test skips itself, with a message, when no CLI is found.

## Release

The extension version must equal the Python package version and the tag; the `verify` job in
[`release.yml`](../.github/workflows/release.yml) enforces it. After PyPI publishing, the release
workflow attaches the `.vsix` to the GitHub release and publishes it to the Visual Studio
Marketplace and Open VSX. This needs a `vscode-marketplace` environment with the secrets
`VSCE_PAT` (Azure DevOps token for the Marketplace publisher) and `OVSX_PAT` (Open VSX token).

## Safety rules for contributors

- Use `execFile` with an argument array. Never build a shell command from a path or rule ID.
- Never add `--yes` anywhere except after a confirmed preview.
- Anything that changes files or Git hooks must check `vscode.workspace.isTrusted`.
