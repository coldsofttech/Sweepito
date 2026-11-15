const assert = require("node:assert");
const vscode = require("vscode");

suite("Report commands", () => {
    suiteSetup(async () => {
        await vscode.extensions.getExtension("coldsofttech.sweepito").activate();
    });

    test("registers the report, config, rules and JSON commands", async () => {
        const commands = await vscode.commands.getCommands(true);
        for (const id of [
            "sweepito.report",
            "sweepito.doctor",
            "sweepito.showConfig",
            "sweepito.validateConfig",
            "sweepito.createConfig",
            "sweepito.listRules",
            "sweepito.listProfiles",
            "sweepito.explainRule",
            "sweepito.explainProfile",
            "sweepito.openJson",
            "sweepito.copyJson",
        ]) {
            assert.ok(commands.includes(id), `${id} is registered`);
        }
    });

    test("Doctor opens its result as a Markdown document", async () => {
        await vscode.commands.executeCommand("sweepito.doctor");
        // The command also opens a preview, which takes the focus, so look at the open documents.
        const doc = vscode.workspace.textDocuments.find(
            (d) => d.languageId === "markdown" && /healthy/i.test(d.getText()),
        );
        assert.ok(doc, "a Markdown document with the doctor result is open");
    });
});
