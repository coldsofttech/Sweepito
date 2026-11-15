const assert = require("node:assert");
const vscode = require("vscode");

suite("Hook commands", () => {
    suiteSetup(async () => {
        await vscode.extensions.getExtension("coldsofttech.sweepito").activate();
    });

    test("registers the install, uninstall and status commands", async () => {
        const commands = await vscode.commands.getCommands(true);
        for (const id of ["sweepito.installHook", "sweepito.uninstallHook", "sweepito.hookStatus"]) {
            assert.ok(commands.includes(id), `${id} is registered`);
        }
    });

    test("hook status in a folder that is not a Git repository shows an error instead of throwing", async () => {
        await vscode.commands.executeCommand("sweepito.hookStatus");
    });
});
