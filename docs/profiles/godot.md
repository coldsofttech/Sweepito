# godot

[Back to all profiles](../profiles.md)

Godot projects

**Detected by:** `project.godot`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `godot.cache` | `/.godot/` | `project.godot` | safe | Editor import cache (recreated when the project is opened) |

## Configuration

```toml
[clean]
enable = ["godot.cache"]
```

Command-line equivalent:

```bash
sweepito clean -p godot
```

Notes:

- `.godot/` is recreated when the project is next opened in the editor.
