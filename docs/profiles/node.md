# node

[Back to all profiles](../profiles.md)

Node.js, React, Next.js, Vue, Nuxt, Angular, Vite, Svelte, Astro

**Detected by:** `package.json`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `node.eslint` | `.eslintcache` | `package.json` | safe | ESLint cache |
| `node.tsbuildinfo` | `*.tsbuildinfo` | `package.json` | safe | TypeScript incremental build info |
| `node.modules-cache` | `node_modules/.cache/` | `package.json` | safe | Babel, webpack and ESLint caches inside node_modules |
| `node.vite` | `.vite/` | `package.json` | safe | Vite cache |
| `node.turbo` | `.turbo/` | `package.json` | safe | Turborepo local cache |
| `node.parcel` | `.parcel-cache/` | `package.json` | safe | Parcel cache |
| `node.angular-cache` | `.angular/cache/` | `angular.json` | safe | Angular CLI cache |
| `node.astro` | `.astro/` | `astro.config.*` | safe | Astro generated types and cache |
| `node.next` | `/.next/` | `next.config.*` | configurable | Next.js build output |
| `node.nuxt` | `/.nuxt/`, `/.output/` | `nuxt.config.*` | configurable | Nuxt build output |
| `node.svelte-kit` | `/.svelte-kit/` | `svelte.config.*` | configurable | SvelteKit generated output |
| `node.dist` | `/dist/` | `package.json` | configurable | Build and distribution output |
| `node.build` | `/build/`, `/out/` | `package.json` | configurable | Build output and static exports |
| `node.coverage` | `/coverage/` | `package.json` | configurable | Test coverage reports |
| `node.modules` | `/node_modules/` | `package.json` | high-impact | Installed dependencies (requires reinstall) |

## Configuration

```toml
[clean]
enable  = ["node.next", "node.dist", "node.build"]   # framework build output
exclude = ["apps/legacy-admin/"]                      # a project you want untouched

[[rule]]
id = "custom.storybook"
paths = ["/storybook-static/"]
requires = ["package.json"]
```

Command-line equivalent:

```bash
sweepito clean -p node --enable node.next --enable node.nuxt
```

Notes:

- Framework rules need their config file: `node.next` needs `next.config.*`, `node.nuxt` needs `nuxt.config.*`, `node.svelte-kit` needs `svelte.config.*`, `node.astro` needs `astro.config.*` and `node.angular-cache` needs `angular.json`.
- Monorepos work per package: each directory with its own `package.json` and config is matched separately.
- `node.modules` (`node_modules/`) is `high-impact` and needs `--enable node.modules`. `node_modules/.cache` is a separate `safe` rule.
- When both are selected, `node_modules/` replaces its `.cache` child in the plan.
