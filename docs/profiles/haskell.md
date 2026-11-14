# haskell

[Back to all profiles](../profiles.md)

Haskell: Cabal and Stack

**Detected by:** `*.cabal`, `stack.yaml`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `haskell.dist-newstyle` | `/dist-newstyle/` | `*.cabal` | safe | Cabal build output |
| `haskell.stack-work` | `/.stack-work/` | `stack.yaml` | configurable | Stack build output (holds built dependencies; slow to rebuild) |

## Configuration

```toml
[clean]
enable = ["haskell.stack-work"]
```

Command-line equivalent:

```bash
sweepito clean -p haskell --enable haskell.stack-work
```

Notes:

- `.stack-work/` is `configurable`: it holds built dependencies and can take a long time to rebuild.
- `cabal.project.freeze` and `stack.yaml.lock` are lock files and are never targeted.
