# go

[Back to all profiles](../profiles.md)

Go modules and build tools

**Detected by:** `go.mod`, `go.work`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `go.test-artifacts` | `*.test`, `*.prof`, `coverage.out` | `go.mod`, `go.work` | safe | Compiled test binaries and profiles |
| `go.bin` | `/bin/` | `go.mod`, `go.work` | configurable | Conventional project build output |
| `go.vendor` | `/vendor/` | `go.mod`, `go.work` | high-impact | Vendored dependencies (often committed; tracked files are protected) |
| `go.gocache` | `/.gocache/` | `go.mod`, `go.work` | safe | Project-local Go build cache (GOCACHE pointed at the project, never the user cache) |
| `go.coverage` | `/coverage/` | `go.mod` | configurable | Coverage output folder |

## Configuration

```toml
[clean]
enable = ["go.bin"]
```

Command-line equivalent:

```bash
sweepito clean -p go --enable go.bin
```

Notes:

- `vendor/` is `high-impact` and often committed. Tracked files are protected, so a committed `vendor/` is never touched.
- The Go build and module caches are global; use `go clean -cache` for those. Sweepito does not manage them.
