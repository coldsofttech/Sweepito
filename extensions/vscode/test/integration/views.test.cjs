const assert = require("node:assert");
const vscode = require("vscode");

suite("Cleanup candidates view", () => {
    suiteSetup(async () => {
        await vscode.extensions.getExtension("coldsofttech.sweepito").activate();
    });

    test("the view is created and can be focused", async () => {
        // Resolves only when the view id is registered by a tree view.
        await vscode.commands.executeCommand("sweepito.candidates.focus");
    });

    test("Expand All and Collapse All refresh the view without errors", async () => {
        await vscode.commands.executeCommand("sweepito.expandAll");
        await vscode.commands.executeCommand("sweepito.collapseAll");
        await vscode.commands.executeCommand("sweepito.candidates.focus");
    });

    test("the settings menu opens a Quick Pick that can be dismissed", async () => {
        const menu = vscode.commands.executeCommand("sweepito.menu");
        await new Promise((resolve) => setTimeout(resolve, 300));
        await vscode.commands.executeCommand("workbench.action.closeQuickOpen");
        await menu;
    });

    test("Reveal ignores a node without items", async () => {
        await vscode.commands.executeCommand("sweepito.reveal", { items: [] });
        await vscode.commands.executeCommand("sweepito.reveal");
        assert.ok((await vscode.commands.getCommands(true)).includes("sweepito.reveal"));
    });
});
