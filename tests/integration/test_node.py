"""Integration tests for the node profile."""

from tests.integration.support import Case, ProfileSuite

CASE_NODE = Case(
    id="node",
    profile="node",
    markers={
        "angular.json": "{}",
        "astro.config.mjs": "",
        ".storybook/main.js": "",
        "cypress.config.js": "",
        "next.config.js": "",
        "nx.json": "{}",
        "playwright.config.ts": "",
        "rush.json": "{}",
        "vitest.config.ts": "",
        "webpack.config.js": "",
        "nuxt.config.ts": "",
        "package.json": "{}",
        "svelte.config.js": "",
    },
    targets={
        "node.angular-cache": [".angular/cache/"],
        "node.astro": [".astro/"],
        "node.build": ["build/", "out/"],
        "node.coverage": ["coverage/"],
        "node.dist": ["dist/"],
        "node.eslint": [".eslintcache"],
        "node.modules-cache": ["node_modules/.cache/"],
        "node.cypress": ["cypress/videos/", "cypress/screenshots/"],
        "node.next": [".next/"],
        "node.nx": [".nx/cache/"],
        "node.playwright": ["test-results/", "playwright-report/"],
        "node.rush-temp": ["common/temp/"],
        "node.storybook": ["storybook-static/"],
        "node.vitest": [".vitest/"],
        "node.webpack": [".cache/webpack/"],
        "node.nuxt": [".nuxt/", ".output/"],
        "node.parcel": [".parcel-cache/"],
        "node.svelte-kit": [".svelte-kit/"],
        "node.tsbuildinfo": ["tsconfig.tsbuildinfo"],
        "node.turbo": [".turbo/"],
        "node.vite": [".vite/"],
    },
    blocked_without={
        "node.angular-cache": ["angular.json"],
        "node.astro": ["astro.config.mjs"],
        "node.cypress": ["cypress.config.js"],
        "node.next": ["next.config.js"],
        "node.nx": ["nx.json"],
        "node.playwright": ["playwright.config.ts"],
        "node.rush-temp": ["rush.json"],
        "node.storybook": [".storybook/main.js"],
        "node.vitest": ["vitest.config.ts"],
        "node.webpack": ["webpack.config.js"],
        "node.nuxt": ["nuxt.config.ts"],
        "node.svelte-kit": ["svelte.config.js"],
    },
)

CASE_NODE_MODULES = Case(
    id="node-modules",
    profile="node",
    markers={"package.json": "{}"},
    targets={"node.modules": ["node_modules/"]},
    blocked_without={},
)

CASES = [CASE_NODE, CASE_NODE_MODULES]


class TestNode(ProfileSuite):
    case = CASE_NODE


class TestNodeModules(ProfileSuite):
    case = CASE_NODE_MODULES
