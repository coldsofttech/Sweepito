// @ts-check
import * as vscode from "vscode";

/**
 * The actions in the view's settings menu, grouped under separators. The other commands stay in
 * the Command Palette; this is the short list a user reaches for from the sidebar.
 * @type {({ label: string, description?: string, command: string, args?: any[] } | { label: string, separator: true })[]}
 */
const ACTIONS = [
    { label: "Cleanup", separator: true },
    { label: "$(refresh) Scan", description: "Look for cleanup candidates", command: "sweepito.scan" },
    { label: "$(trash) Clean", description: "Remove the candidates, after asking", command: "sweepito.clean" },
    {
        label: "$(shield) Choose Risk Level",
        description: "For this session",
        command: "sweepito.setRisk",
    },
    { label: "Health", separator: true },
    { label: "$(pulse) Doctor", description: "Check Git, configuration and hooks", command: "sweepito.doctor" },
    { label: "$(check) Check", description: "Scan and report whether anything is left", command: "sweepito.check" },
    {
        label: "$(graph) Report",
        description: "Reclaimable space by profile, rule and risk",
        command: "sweepito.report",
    },
    { label: "Configuration", separator: true },
    {
        label: "$(settings) Open Settings",
        description: "Sweepito settings",
        command: "workbench.action.openSettings",
        args: ["@ext:coldsofttech.sweepito"],
    },
    {
        label: "$(new-file) Create Config File",
        description: "Write a starter sweepito.toml",
        command: "sweepito.createConfig",
    },
    { label: "$(eye) Show Effective Configuration", command: "sweepito.showConfig" },
    { label: "$(verified) Validate Configuration", command: "sweepito.validateConfig" },
    { label: "Rules and profiles", separator: true },
    { label: "$(list-unordered) List Rules", command: "sweepito.listRules" },
    { label: "$(list-tree) List Profiles", command: "sweepito.listProfiles" },
    { label: "Git hook", separator: true },
    { label: "$(git-commit) Install Git Hook", command: "sweepito.installHook" },
    { label: "$(trash) Uninstall Git Hook", command: "sweepito.uninstallHook" },
    { label: "$(info) Show Git Hook Status", command: "sweepito.hookStatus" },
    { label: "Output", separator: true },
    { label: "$(output) Show Output", command: "sweepito.showOutput" },
    { label: "$(terminal) Show Terminal", command: "sweepito.showTerminal" },
    { label: "$(json) Open Result as JSON", command: "sweepito.openJson" },
    { label: "$(copy) Copy Result as JSON", command: "sweepito.copyJson" },
];

/** Shows the settings menu as a native Quick Pick and runs the chosen action. */
export async function showMenu() {
    const items = ACTIONS.map((action) =>
        "separator" in action
            ? { label: action.label, kind: vscode.QuickPickItemKind.Separator }
            : { label: action.label, description: action.description, action },
    );
    const picked = /** @type {any} */ (
        await vscode.window.showQuickPick(items, { title: "Sweepito", placeHolder: "Choose an action" })
    );
    if (!picked?.action) return;
    await vscode.commands.executeCommand(picked.action.command, ...(picked.action.args ?? []));
}
