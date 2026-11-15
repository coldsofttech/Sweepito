# node-pm

[Back to all profiles](../profiles.md)

npm, pnpm, Yarn and Bun project-local stores

**Detected by:** `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `bun.lock`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `node-pm.yarn-cache` | `/.yarn/cache/` | `yarn.lock` | configurable | Yarn offline cache (skipped automatically when tracked) |
| `node-pm.pnpm-store` | `/.pnpm-store/` | `pnpm-lock.yaml` | high-impact | Local pnpm content-addressable store |
| `node-pm.yarn-unplugged` | `/.yarn/unplugged/`, `/.yarn/install-state.gz`, `/.yarn/build-state.yml` | `yarn.lock` | high-impact | Extracted Yarn dependencies and install state (yarn install required again) |

## Configuration

```toml
[clean]
enable = ["node-pm.yarn-cache"]
```

Command-line equivalent:

```bash
sweepito clean -p node-pm --enable node-pm.yarn-cache
```

Notes:

- Yarn zero-install repositories commit `.yarn/cache`. Tracked files are never removed, so that cache is skipped automatically.
- The pnpm store (`.pnpm-store/`) is `high-impact`.
- Global package manager caches (`~/.npm`, `~/.cache/yarn`) are out of scope.
