import { defineConfig } from "@vscode/test-cli";

export default defineConfig({
    files: "test/integration/**/*.test.cjs",
    workspaceFolder: "./test/integration/workspace",
    // The macOS runners are slow, and Mocha's default of 2 seconds is too short for a command that
    // opens a preview.
    mocha: { ui: "tdd", timeout: 20000 },
});
