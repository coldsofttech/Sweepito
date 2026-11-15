const assert = require("node:assert");
const vscode = require("vscode");

suite("Sweepito extension", () => {
    suiteSetup(async () => {
        await vscode.extensions.getExtension("coldsofttech.sweepito").activate();
    });

    test("registers its commands", async () => {
        const commands = await vscode.commands.getCommands(true);
        for (const id of [
            "sweepito.scan",
            "sweepito.clean",
            "sweepito.setRisk",
            "sweepito.expandAll",
            "sweepito.collapseAll",
            "sweepito.menu",
        ]) {
            assert.ok(commands.includes(id), `${id} is registered`);
        }
    });

    test("defaults to the safe risk level", () => {
        assert.strictEqual(vscode.workspace.getConfiguration("sweepito").get("risk"), "safe");
    });
});
