const assert = require("node:assert");
const vscode = require("vscode");

suite("Scanning commands", () => {
    suiteSetup(async () => {
        await vscode.extensions.getExtension("coldsofttech.sweepito").activate();
    });

    test("registers the scan, check, clean and risk commands", async () => {
        const commands = await vscode.commands.getCommands(true);
        for (const id of [
            "sweepito.scan",
            "sweepito.check",
            "sweepito.clean",
            "sweepito.cleanWorkspace",
            "sweepito.cleanProfile",
            "sweepito.cleanRule",
            "sweepito.cleanFolder",
            "sweepito.setRisk",
        ]) {
            assert.ok(commands.includes(id), `${id} is registered`);
        }
    });

    test("Scan finishes even when the folder cannot be scanned", async () => {
        await vscode.commands.executeCommand("sweepito.scan");
    });

    test("Clean with nothing to clean does nothing", async () => {
        await vscode.commands.executeCommand("sweepito.clean");
    });
});
