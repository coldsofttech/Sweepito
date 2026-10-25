"""Integration tests for the node profile."""

from tests.integration.support import Case, ProfileSuite

CASE_NODE = Case(
    id="node",
    profile="node",
    markers={
        "angular.json": "{}",
        "astro.config.mjs": "",
        "next.config.js": "",
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
        "node.next": [".next/"],
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
        "node.next": ["next.config.js"],
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
