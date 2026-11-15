import { defineConfig } from "@vscode/test-cli";

export default defineConfig({
    files: "test/integration/**/*.test.cjs",
    workspaceFolder: "./test/integration/workspace",
});
