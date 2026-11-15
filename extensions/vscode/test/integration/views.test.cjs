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

    test("Reveal ignores a node without items", async () => {
        await vscode.commands.executeCommand("sweepito.reveal", { items: [] });
        await vscode.commands.executeCommand("sweepito.reveal");
        assert.ok((await vscode.commands.getCommands(true)).includes("sweepito.reveal"));
    });
});
