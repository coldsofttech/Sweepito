// @ts-check
import path from "node:path";
import * as vscode from "vscode";
import { hookStatus, installHook, uninstallHook } from "./hook-commands";
import { showTerminal } from "./output";
import {
    createConfigFile,
    explainProfile,
    explainRule,
    jsonCommand,
    listProfiles,
    listRules,
    runDoctor,
    showConfig,
    showReport,
    validateConfiguration,
} from "./reports";
import { check, chooseRisk, clean, scan } from "./scanning";
import { allCandidates, changed, state } from "./state";
import { CandidatesProvider, renderStatus } from "./views";

const RESCAN_SETTINGS = [
    "risk",
    "profiles",
    "enableRules",
    "disableRules",
    "exclude",
    "noGitCheck",
    "customRules",
    "customProfiles",
    "configFile",
];

/** @param {vscode.ExtensionContext} context */
export function activate(context) {
    state.extensionPath = context.extensionPath;
    state.extensionVersion = context.extension.packageJSON.version;
    state.statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
    state.statusBar.command = "sweepito.scan";
    const output = vscode.window.createOutputChannel("Sweepito");
    state.output = output;
    /** @type {ReturnType<typeof setTimeout> | undefined} */
    let rescanTimer;
    const watcher = vscode.workspace.createFileSystemWatcher("**/{sweepito.toml,.sweepito.toml,pyproject.toml}");
    const rescanSoon = () => {
        clearTimeout(rescanTimer);
        rescanTimer = setTimeout(() => scan({ quiet: true }), 500);
    };
    watcher.onDidChange(rescanSoon);
    watcher.onDidCreate(rescanSoon);
    watcher.onDidDelete(rescanSoon);
    context.subscriptions.push({
        dispose: () => {
            state.terminal?.dispose();
            state.terminalWriter?.dispose();
        },
    });
    context.subscriptions.push(watcher, output, { dispose: () => clearTimeout(rescanTimer) });

    const register = (/** @type {string} */ id, /** @type {(...args: any[]) => any} */ fn) =>
        context.subscriptions.push(vscode.commands.registerCommand(id, fn));
    register("sweepito.scan", () => scan());
    register("sweepito.check", check);
    register("sweepito.clean", () => clean(allCandidates(), "this workspace"));
    register("sweepito.cleanWorkspace", (node) => clean(node.items, `folder ${node.label}`));
    register("sweepito.cleanProfile", (node) => clean(node.items, `profile ${node.label}`));
    register("sweepito.cleanRule", (node) => clean(node.items, `rule ${node.label}`));
    register("sweepito.cleanFolder", (node) => clean(node.items, node.label));
    register("sweepito.report", showReport);
    register("sweepito.openJson", () => jsonCommand("open"));
    register("sweepito.copyJson", () => jsonCommand("copy"));
    register("sweepito.showOutput", () => output.show(true));
    register("sweepito.showTerminal", showTerminal);
    register("sweepito.createConfig", createConfigFile);
    register("sweepito.showConfig", showConfig);
    register("sweepito.validateConfig", validateConfiguration);
    register("sweepito.doctor", runDoctor);
    register("sweepito.installHook", installHook);
    register("sweepito.uninstallHook", uninstallHook);
    register("sweepito.hookStatus", hookStatus);
    register("sweepito.listRules", listRules);
    register("sweepito.listProfiles", listProfiles);
    register("sweepito.explainRule", explainRule);
    register("sweepito.explainProfile", explainProfile);
    register("sweepito.setRisk", chooseRisk);
    register("sweepito.reveal", (node) => {
        const item = node?.items?.[0];
        if (item) {
            vscode.commands.executeCommand("revealFileInOS", vscode.Uri.file(path.join(item.folder, item.path)));
        }
    });

    context.subscriptions.push(
        state.statusBar,
        changed,
        vscode.window.createTreeView("sweepito.candidates", { treeDataProvider: new CandidatesProvider() }),
        vscode.workspace.onDidChangeWorkspaceFolders(() => scan({ quiet: true })),
        vscode.workspace.onDidChangeConfiguration((e) => {
            if (!e.affectsConfiguration("sweepito")) return;
            renderStatus();
            if (RESCAN_SETTINGS.some((name) => e.affectsConfiguration(`sweepito.${name}`))) {
                scan({ quiet: true });
            }
        }),
    );

    renderStatus();
    // Started after activation returns; the scan itself is asynchronous.
    if (vscode.workspace.getConfiguration("sweepito").get("autoScan", true)) {
        setImmediate(() => scan({ quiet: true }));
    }
}

export function deactivate() {}
