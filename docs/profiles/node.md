# node

[Back to all profiles](../profiles.md)

Node.js, React, Next.js, Vue, Nuxt, Angular, Vite, Svelte, Astro, Nx, Vitest, Storybook, Webpack, Playwright, Cypress, Rush

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
| `node.nx` | `/.nx/cache/` | `nx.json` | safe | Nx computation cache |
| `node.vitest` | `/.vitest/` | `vitest.config.*` | safe | Vitest cache |
| `node.storybook` | `/storybook-static/` | `.storybook/main.*` | safe | Storybook static build |
| `node.webpack` | `/.cache/webpack/` | `webpack.config.*` | safe | Webpack filesystem cache |
| `node.next` | `/.next/` | `next.config.*` | configurable | Next.js build output |
| `node.nuxt` | `/.nuxt/`, `/.output/` | `nuxt.config.*` | configurable | Nuxt build output |
| `node.svelte-kit` | `/.svelte-kit/` | `svelte.config.*` | configurable | SvelteKit generated output |
| `node.playwright` | `/test-results/`, `/playwright-report/` | `playwright.config.*` | configurable | Playwright test results and reports (may be needed to debug failures) |
| `node.cypress` | `/cypress/videos/`, `/cypress/screenshots/` | `cypress.config.*` | configurable | Cypress videos and screenshots (may be needed to debug failures) |
| `node.rush-temp` | `/common/temp/` | `rush.json` | configurable | Rush temporary install files (rush install recreates them) |
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
id = "custom.jest-cache"
paths = ["/.jest-cache/"]       # only if your jest.config sets cacheDirectory here
requires = ["jest.config.*"]
```

Command-line equivalent:

```bash
sweepito clean -p node --enable node.next --enable node.nuxt
```

Notes:

- Framework rules need their config file: `node.next` needs `next.config.*`, `node.nuxt` needs `nuxt.config.*`, `node.svelte-kit` needs `svelte.config.*`, `node.astro` needs `astro.config.*` and `node.angular-cache` needs `angular.json`.
- Tool rules need their own marker: `node.nx` needs `nx.json`, `node.vitest` needs `vitest.config.*`, `node.storybook` needs `.storybook/main.*`, `node.webpack` needs `webpack.config.*`, `node.playwright` needs `playwright.config.*`, `node.cypress` needs `cypress.config.*` and `node.rush-temp` needs `rush.json`.
- Playwright and Cypress outputs can be the only evidence of a failing run, so `node.playwright` and `node.cypress` are `configurable` (opt-in). `node.rush-temp` holds Rush's install files, so it is also opt-in.
- Jest and Lerna have no rule: Jest caches in the system temp dir by default and `.lerna/` is not a confirmed generated directory. Add a custom rule if your project sets a local `cacheDirectory`.
- Monorepos work per package: each directory with its own `package.json` and config is matched separately.
- `node.modules` (`node_modules/`) is `high-impact` and needs `--enable node.modules`. `node_modules/.cache` is a separate `safe` rule.
- When both are selected, `node_modules/` replaces its `.cache` child in the plan.
