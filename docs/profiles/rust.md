# rust

[Back to all profiles](../profiles.md)

Rust and Cargo

**Detected by:** `Cargo.toml`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `rust.target` | `/target/` | `Cargo.toml` | configurable | Cargo build output (slow to rebuild) |
| `rust.profiling` | `flamegraph.svg`, `perf.data`, `perf.data.*` | `Cargo.toml` | configurable | Profiling output |

## Configuration

```toml
[clean]
enable  = ["rust.target"]
exclude = ["tools/benchmarks/"]   # keep expensive-to-rebuild benchmark workspaces
```

Command-line equivalent:

```bash
sweepito clean -p rust --enable rust.target
```

Notes:

- `target/` can reach several GB and takes minutes to rebuild, so it is `configurable` rather than `safe`.
- Cargo workspaces share one `target/` at the workspace root; it is matched beside the `Cargo.toml` that contains it.
- `~/.cargo` registry caches are global and out of scope.
