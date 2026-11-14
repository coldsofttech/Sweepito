# common

[Back to all profiles](../profiles.md)

OS and editor artifacts that apply to any project

**Detected by:** always active

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `common.os-junk` | `.DS_Store`, `Thumbs.db`, `desktop.ini` | - | safe | Operating system metadata files |
| `common.pm-logs` | `npm-debug.log*`, `yarn-error.log*`, `pnpm-debug.log*` | - | safe | Package manager debug logs |
| `common.editor-temp` | `*.swp`, `*.swo`, `*~` | - | configurable | Editor swap files (may hold unsaved recovery data) |
| `common.merge-leftovers` | `*.orig`, `*.rej` | - | configurable | Merge and patch leftovers |
| `common.logs` | `*.log` | - | configurable | Generic log files |

## Configuration

```toml
[clean]
enable  = ["common.logs", "common.editor-temp"]
disable = ["common.os-junk"]
```

Command-line equivalent:

```bash
sweepito clean --enable common.logs
```

Notes:

- Always active, even without markers, and applies to every project.
- `*.log` is `configurable` because logs are sometimes intentional.
- Editor swap files can hold unsaved recovery data, so `common.editor-temp` is opt-in.
- IDE settings (`.idea/`, `.vscode/`) and `.env*` files are never targeted.
