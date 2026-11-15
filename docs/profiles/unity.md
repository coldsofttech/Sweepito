# unity

[Back to all profiles](../profiles.md)

Unity projects

**Detected by:** `ProjectSettings/ProjectVersion.txt`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `unity.temp` | `/Temp/` | `ProjectSettings/ProjectVersion.txt` | safe | Editor temporary files |
| `unity.obj` | `/obj/` | `ProjectSettings/ProjectVersion.txt` | configurable | Generated C# project build output |
| `unity.library` | `/Library/` | `ProjectSettings/ProjectVersion.txt` | high-impact | Asset import cache (can take hours to rebuild on large projects) |

## Configuration

```toml
[clean]
enable = ["unity.library"]
```

Command-line equivalent:

```bash
sweepito clean -p unity --enable unity.library
```

Notes:

- `Library/` is the asset import cache and can take hours to rebuild on large projects, so it is `configurable`.
- `Assets/`, `Packages/` and `ProjectSettings/` are never targeted.
