# batchvault

[Back to all profiles](../profiles.md)

BatchVault archives (archive output, manifests, signatures and keys are never cleaned)

**Detected by:** `batchvault.toml`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `batchvault.staging` | `.batchvault-*/` | `batchvault.toml` | configurable | Staging folders left by an interrupted run (an active run also uses one) |
| `batchvault.manifest-tmp` | `manifest.json.*.tmp` | `batchvault.toml` | configurable | Partial manifest written when a run was killed (the real manifest is untouched) |

## Configuration

```toml
[clean]
enable = ["batchvault.staging", "batchvault.manifest-tmp"]
```

Command-line equivalent:

```bash
sweepito clean -p batchvault --enable batchvault.staging
```

Notes:

- Both rules are opt-in: an active BatchVault run also uses a `.batchvault-*` staging folder and Sweepito cannot tell it from a dead one. Run them only when no BatchVault run is active.
- Staging folders sit inside the pack or unpack destination (for example `archives/`), so they are found only when that folder is git-ignored.
- Archive output (`archives/`, `restored/`, `*.bv.NNN`, `*.7z.NNN`), manifests, signatures, keys and restored files are never targeted.
- The profile is detected from `batchvault.toml`; `[tool.batchvault]` in `pyproject.toml` is not detectable because markers match file names only.
