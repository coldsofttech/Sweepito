# Sweepito for VS Code

Safely clean caches and build artifacts without leaving the editor. This extension is a thin
front end for the [Sweepito](https://github.com/coldsofttech/Sweepito) command line tool. It
shows what `sweepito scan` finds, and every removal goes through `sweepito clean`. The
extension never deletes files itself, so Sweepito's safety model applies unchanged: only
git-ignored, untracked paths inside the project root are removed.

## Requirements

The extension needs the Sweepito CLI (version 0.1.0 or newer), which is a Python package.
You need **Python 3.11 or newer** to install it:

```bash
pipx install sweepito        # or: uv tool install sweepito
```

If the CLI is not found, the extension says so and offers to run the install in a terminal.
It looks for the CLI in this order:

1. The `sweepito.executablePath` setting.
2. `sweepito` on your `PATH`.
3. The active Python environment (`python -m sweepito`), via the Python extension.

## Using it

1. Open a Git repository folder.
2. Click the **Sweepito** icon in the Activity Bar. The tree lists cleanup candidates grouped
   by profile and rule, with the risk level and size of each. The status bar shows the total.
3. Clean from the tree (the trash icon on a folder, profile or rule), or run
   **Sweepito: Clean** from the Command Palette.
4. A confirmation lists exactly what will be removed. Nothing is deleted before you agree.

Only `safe` rules are scanned by default. To include `configurable` or `high-impact` rules, use
**Sweepito: Choose Risk Level for This Session**, or set `sweepito.risk`. Removing
higher-risk items always needs a separate, explicit confirmation, and high-impact items ask a
second time.

### Commands

| Command | What it does |
|---|---|
| `Sweepito: Scan` | Rescan the workspace folders |
| `Sweepito: Clean` | Clean all safe items, or everything your settings select, after confirmation |
| `Sweepito: Choose Risk Level for This Session` | Temporarily include higher-risk rules in the scan |
| `Sweepito: Doctor` | Run `sweepito doctor` and show the result in the Sweepito output |
| `Sweepito: Install Git Hook` / `Uninstall Git Hook` | Manage the native Git hook (`post-commit` or `pre-commit`) |
| `Sweepito: Open Config File` / `Create Config File` | Open `sweepito.toml` (or `[tool.sweepito]`), or create one with `sweepito init` |

With several workspace folders, each folder is scanned separately and the tree groups results
by folder.

## Custom rules and configuration

Rules, profiles and custom path rules live in the same place as for the command line:
`sweepito.toml`, `.sweepito.toml`, or a `[tool.sweepito]` table in `pyproject.toml`. See the
[configuration reference](https://github.com/coldsofttech/Sweepito/blob/main/docs/configuration.md).
Custom rules appear in the tree automatically. Use **Sweepito: Create Config File** to get a
starter file.

The extension settings below are translated into command line flags and are combined with the
config file, as the CLI does.

| Setting | CLI flag | Default |
|---|---|---|
| `sweepito.executablePath` | | empty (search `PATH`, then the Python environment) |
| `sweepito.risk` | `--risk` | `safe` |
| `sweepito.enableRules` | `--enable` | `[]` |
| `sweepito.disableRules` | `--disable` | `[]` |
| `sweepito.exclude` | `--exclude` | `[]` |
| `sweepito.configFile` | `--config` | empty (search upward) |
| `sweepito.autoScan` | | `true` |
| `sweepito.statusBar.enabled` | | `true` |

## Untrusted workspaces

In an untrusted workspace the extension runs in a limited mode. Scan and Doctor work. Clean,
Install/Uninstall Git Hook and Create Config File are disabled, and the workspace's
`sweepito.executablePath` and Python environment are ignored, because they could run code from
the workspace.

## Limits

- Cleaning works on a folder, a profile, or a single rule. Selecting individual paths is not
  supported yet.
- Local folders only (no virtual workspaces).

## Development

See [docs/vscode.md](https://github.com/coldsofttech/Sweepito/blob/main/docs/vscode.md).
