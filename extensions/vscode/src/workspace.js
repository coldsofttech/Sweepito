// @ts-check
import * as vscode from "vscode";
import * as git from "./core/git";
import { log, showMarkdown } from "./output";
import { errorMessage, folders, state } from "./state";

/**
 * The value of a setting only when the user set it, so a config file can supply the default.
 * @param {vscode.WorkspaceConfiguration} config
 * @param {string} key
 */
function explicit(config, key) {
    const info = config.inspect(key);
    const set = info?.workspaceFolderValue ?? info?.workspaceValue ?? info?.globalValue;
    return set === undefined ? undefined : config.get(key);
}

/**
 * The settings for one folder (VS Code resolves per-folder values).
 * @param {string} root
 */
export function settings(root) {
    const config = vscode.workspace.getConfiguration("sweepito", vscode.Uri.file(root));
    return {
        profiles: explicit(config, "profiles"),
        risk: state.sessionRisk ?? explicit(config, "risk"),
        customRules: config.get("customRules", []),
        customProfiles: config.get("customProfiles", {}),
        enable: config.get("enableRules", []),
        disable: config.get("disableRules", []),
        exclude: config.get("exclude", []),
        noGitCheck: vscode.workspace.isTrusted && config.get("noGitCheck", false),
    };
}

export const configFileSetting = (/** @type {string} */ root) =>
    vscode.workspace.isTrusted
        ? vscode.workspace.getConfiguration("sweepito", vscode.Uri.file(root)).get("configFile", "")
        : "";

/** The workspace folder to act on: the only one, or one picked from a list. Null if none. */
export async function pickFolder(/** @type {string} */ title = "Which folder?") {
    const list = folders();
    if (list.length === 0) {
        vscode.window.showInformationMessage("Sweepito: open a folder first.");
        return null;
    }
    if (list.length === 1) return list[0].uri.fsPath;
    const picked = await vscode.window.showQuickPick(
        list.map((f) => ({ label: f.name, description: f.uri.fsPath })),
        { title },
    );
    return picked?.description ?? null;
}

/**
 * Runs `task` for a workspace folder and shows the Markdown it returns, or any failure.
 * @param {string} title
 * @param {(root: string) => Promise<string | null | undefined>} task
 */
export async function withWorkspace(title, task) {
    const root = await pickFolder();
    if (!root) return;
    try {
        const content = await vscode.window.withProgress(
            { location: vscode.ProgressLocation.Notification, title: `Sweepito: ${title}` },
            () => task(root),
        );
        if (content) await showMarkdown(content);
    } catch (error) {
        log(`${title} failed: ${errorMessage(error)}`, { error: true });
        vscode.window.showErrorMessage(`Sweepito: ${errorMessage(error)}`);
    }
}

/**
 * Runs `action` with the root of a Git repository, showing failures.
 * @param {(root: string) => Promise<unknown>} action
 */
export async function withRepo(action) {
    const root = await pickFolder("Which folder's Git hook?");
    if (!root) return;
    try {
        if ((await git.toplevel(root)) === null) throw new Error("Hooks need a Git repository.");
        await action(root);
    } catch (error) {
        log(`Hook command failed: ${errorMessage(error)}`, { error: true });
        vscode.window.showErrorMessage(`Sweepito: ${errorMessage(error)}`);
    }
}

export const requireTrust = () => {
    if (vscode.workspace.isTrusted) return true;
    vscode.window.showWarningMessage("Sweepito cannot change Git hooks or files in an untrusted workspace.");
    return false;
};
