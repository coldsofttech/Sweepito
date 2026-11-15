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

    test("Doctor opens its result as one preview tab, with no editor tab to save", async () => {
        await vscode.commands.executeCommand("sweepito.doctor");
        // The preview opens a moment after the command returns.
        const doctorTabs = async () => {
            for (let attempt = 0; attempt < 100; attempt++) {
                const found = vscode.window.tabGroups.all
                    .flatMap((group) => group.tabs)
                    .filter((tab) => /doctor/i.test(tab.label));
                if (found.length > 0) return found;
                await new Promise((resolve) => setTimeout(resolve, 100));
            }
            return [];
        };
        const tabsFound = await doctorTabs();
        // VS Code may drop a document that no editor shows, so load it again by its address.
        const doc = await vscode.workspace.openTextDocument(
            vscode.Uri.from({ scheme: "sweepito-doc", path: "/Sweepito doctor.md" }),
        );
        assert.ok(/sweepito doctor/i.test(doc.getText()), "the doctor result is held in a read-only document");
        assert.ok(!doc.isDirty && !doc.isUntitled, "there is nothing to save");
        assert.strictEqual(tabsFound.length, 1, "exactly one tab shows the result");
        assert.ok(tabsFound[0].input instanceof vscode.TabInputWebview, "and it is the rendered preview");
    });
});
