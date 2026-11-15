import js from "@eslint/js";
import globals from "globals";

export default [
    { ignores: ["dist/", "node_modules/", ".vscode-test/", "coverage/", "test/integration/workspace/"] },
    js.configs.recommended,
    {
        languageOptions: { ecmaVersion: 2022, sourceType: "module", globals: globals.node },
    },
    {
        // Integration tests run in the extension host without a bundler, with Mocha's TDD globals.
        files: ["test/integration/**/*.cjs"],
        languageOptions: { sourceType: "commonjs", globals: { ...globals.node, ...globals.mocha } },
    },
];
