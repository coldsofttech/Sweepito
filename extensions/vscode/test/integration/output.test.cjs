const assert = require("node:assert");
const vscode = require("vscode");

suite("Output and terminal", () => {
    suiteSetup(async () => {
        await vscode.extensions.getExtension("coldsofttech.sweepito").activate();
    });

    test("registers the output and terminal commands", async () => {
        const commands = await vscode.commands.getCommands(true);
        for (const id of ["sweepito.showOutput", "sweepito.showTerminal"]) {
            assert.ok(commands.includes(id), `${id} is registered`);
        }
    });

    test("Show Terminal opens one extension-owned terminal and reuses it", async () => {
        const named = () => vscode.window.terminals.filter((t) => t.name === "Sweepito");
        await vscode.commands.executeCommand("sweepito.showTerminal");
        assert.strictEqual(named().length, 1);
        await vscode.commands.executeCommand("sweepito.showTerminal");
        assert.strictEqual(named().length, 1);
    });
});
