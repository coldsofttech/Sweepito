# unreal

[Back to all profiles](../profiles.md)

Unreal Engine projects

**Detected by:** `*.uproject`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `unreal.intermediate` | `/Intermediate/` | `*.uproject` | configurable | Generated intermediate build files (needs engine and compiler to rebuild) |
| `unreal.binaries` | `/Binaries/` | `*.uproject` | configurable | Compiled binaries (needs engine and compiler to rebuild) |

## Configuration

```toml
[clean]
enable = ["unreal.intermediate", "unreal.binaries"]
```

Command-line equivalent:

```bash
sweepito clean -p unreal --enable unreal.intermediate
```

Notes:

- Rebuilding needs the engine and a compiler toolchain, so both rules are `configurable`.
- `Saved/` is deliberately not targeted: it holds autosaves, crash dumps, config and local save data.
- `Content/` and `Config/` are never targeted.
