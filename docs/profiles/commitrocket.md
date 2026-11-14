# commitrocket

[Back to all profiles](../profiles.md)

CommitRocket (batched commit and push; the resume journal in .git is never touched)

**Detected by:** `commitrocket.toml`, `.commitrocketignore`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `commitrocket.report-tmp` | `*.json.*.tmp` | `commitrocket.toml`, `.commitrocketignore` | safe | Partial JSON report left by a killed run (the next run rewrites it) |

## Configuration

```toml
[clean]
disable = ["commitrocket.report-tmp"]
```

Command-line equivalent:

```bash
sweepito clean -p commitrocket
```

Notes:

- `commitrocket.report-tmp` removes `<report>.json.<random>.tmp`, the partial copy of a `--report` file left only if a run is killed mid-write. The next run rewrites the report.
- Never targeted: `.git/commitrocket-journal.json` (resume journal), `.gitattributes`, `.lfsconfig`, `commitrocket.toml`, `.commitrocketignore`, the `--report` output itself, and any file CommitRocket has not yet committed.
- Per-run logs live in a per-user folder outside the project, so they are out of scope. A report not named `*.json` needs a custom rule.
