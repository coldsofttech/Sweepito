// @ts-check
import * as vscode from "vscode";
import { catalog, prepare, report as buildWorkspaceReport, scan as scanWorkspace } from "./core/api";
import { RISKS as RISK_LEVELS, profileMarkdown, profilesMarkdown, ruleMarkdown, rulesMarkdown } from "./core/catalog";
import { doctorMarkdown, runChecks } from "./core/doctor";
import * as git from "./core/git";
import * as hooks from "./core/hooks";
import { configMarkdown, configTarget, createConfig, validateConfig } from "./core/init";
import { cleanJson, configJson, doctorJson, profilesJson, reportJson, rulesJson, scanJson } from "./core/json";
import { formatReport } from "./core/report";
import { checksText, reportText } from "./core/text";
import { checksTerminal, reportTerminal, rulesTerminal } from "./core/terminal";
import { log, showJson, toTerminal } from "./output";
import { errorMessage, lastClean, state } from "./state";
import { configFileSetting, pickFolder, requireTrust, settings, withWorkspace } from "./workspace";

/** Shows reclaimable space by profile, rule and risk in a Markdown preview. */
export const showReport = () =>
    withWorkspace("building report", async (root) => {
        const report = await buildWorkspaceReport(root, settings(root), configFileSetting(root));
        log(reportText(report));
        toTerminal((c) => reportTerminal(report, c));
        return formatReport(report);
    });

/** Runs the environment diagnostics and shows them as Markdown. */
export const runDoctor = () =>
    withWorkspace("running doctor", async (root) => {
        const checks = await runChecks(root, settings(root), configFileSetting(root), state.extensionVersion);
        log(checksText(checks));
        toTerminal((c) => checksTerminal(checks, c));
        return doctorMarkdown(checks);
    });

/** Shows the effective configuration (config file plus VS Code settings) as Markdown. */
export const showConfig = () =>
    withWorkspace("loading configuration", async (root) =>
        configMarkdown(root, settings(root), configFileSetting(root)),
    );

export async function validateConfiguration() {
    const root = await pickFolder();
    if (!root) return;
    try {
        const file = await validateConfig(root, settings(root), configFileSetting(root));
        log(`Configuration OK${file ? ` (${file})` : " (no config file)"}.`);
        vscode.window.showInformationMessage(`Sweepito: configuration OK${file ? ` (${file})` : " (no config file)"}.`);
    } catch (error) {
        log(`Configuration invalid: ${errorMessage(error)}`, { error: true });
        vscode.window.showErrorMessage(`Sweepito: ${errorMessage(error)}`);
    }
}

/** Writes a starter sweepito.toml and opens it, like `sweepito init`. */
export async function createConfigFile() {
    if (!requireTrust()) return;
    const root = await pickFolder("Create the config file in which folder?");
    if (!root) return;
    try {
        const target = await configTarget(root);
        const exists = await vscode.workspace.fs.stat(vscode.Uri.file(target)).then(
            () => true,
            () => false,
        );
        if (exists) {
            const answer = await vscode.window.showWarningMessage(
                `${target} already exists. Overwrite it?`,
                { modal: true },
                "Overwrite",
            );
            if (answer !== "Overwrite") return;
        }
        const written = await createConfig(root, settings(root), configFileSetting(root), { force: exists });
        log(`Wrote ${written}`);
        await vscode.window.showTextDocument(await vscode.workspace.openTextDocument(vscode.Uri.file(written)));
    } catch (error) {
        vscode.window.showErrorMessage(`Sweepito: ${errorMessage(error)}`);
    }
}

const loadRegistry = (/** @type {string} */ root) => catalog(root, settings(root), configFileSetting(root));

export async function listRules() {
    await withWorkspace("loading rules", async (root) => {
        const registry = await loadRegistry(root);
        const profiles = await vscode.window.showQuickPick(
            [...registry.profiles.values()].map((p) => ({ label: p.id, description: p.description })),
            { canPickMany: true, title: "Limit to these profiles (none selected shows all)", matchOnDescription: true },
        );
        if (profiles === undefined) return null;
        const risk = await vscode.window.showQuickPick(["any risk", ...RISK_LEVELS], {
            title: "Limit to a risk level",
        });
        if (risk === undefined) return null;
        const filter = { profiles: profiles.map((p) => p.label), risk: risk === "any risk" ? null : risk };
        toTerminal((c) => rulesTerminal(registry, filter, c));
        return rulesMarkdown(registry, filter);
    });
}

export const listProfiles = () =>
    withWorkspace("loading profiles", async (root) => profilesMarkdown(await loadRegistry(root)));

/**
 * Explains a rule: the one given by a tree item, else one picked from a searchable list.
 * @param {any} [node]
 */
export async function explainRule(node) {
    await withWorkspace("loading rule", async (root) => {
        const registry = await loadRegistry(root);
        let id = node?.kind === "rule" ? node.label : undefined;
        if (!id) {
            const picked = await vscode.window.showQuickPick(
                [...registry.rules.values()].map((r) => ({
                    label: r.id,
                    description: r.profile,
                    detail: r.description,
                })),
                { title: "Explain which rule?", matchOnDescription: true, matchOnDetail: true },
            );
            if (!picked) return null;
            id = picked.label;
        }
        return ruleMarkdown(registry, id);
    });
}

/** @param {any} [node] */
export async function explainProfile(node) {
    await withWorkspace("loading profile", async (root) => {
        const registry = await loadRegistry(root);
        let id = node?.kind === "profile" ? node.label : undefined;
        if (!id) {
            const picked = await vscode.window.showQuickPick(
                [...registry.profiles.values()].map((p) => ({ label: p.id, description: p.description })),
                { title: "Explain which profile?", matchOnDescription: true },
            );
            if (!picked) return null;
            id = picked.label;
        }
        return profileMarkdown(registry, id);
    });
}

const JSON_KINDS = [
    { label: "scan", detail: "What a scan finds, like `sweepito scan --json`" },
    { label: "report", detail: "Reclaimable space by profile, rule and risk" },
    { label: "doctor", detail: "Environment checks" },
    { label: "rules", detail: "Every rule" },
    { label: "profiles", detail: "Every profile" },
    { label: "config", detail: "Effective configuration" },
    { label: "clean", detail: "The last clean in this session, like `sweepito clean --json`" },
    { label: "hooks", detail: "Installed Git hooks" },
];

/**
 * The CLI-shaped JSON for one kind of result in one folder.
 * @param {string} kind
 * @param {string} root
 */
async function jsonFor(kind, root) {
    const vs = settings(root);
    const configFile = configFileSetting(root);
    switch (kind) {
        case "scan":
            return scanJson((await scanWorkspace(root, vs, configFile)).plan);
        case "report":
            return reportJson(await buildWorkspaceReport(root, vs, configFile));
        case "doctor":
            return doctorJson(await runChecks(root, vs, configFile, state.extensionVersion));
        case "rules":
            return rulesJson(await catalog(root, vs, configFile));
        case "profiles":
            return profilesJson(await catalog(root, vs, configFile));
        case "config":
            return configJson(await prepare(root, vs, configFile));
        case "clean": {
            const last = lastClean.get(root);
            if (!last) throw new Error("Nothing has been cleaned in this folder yet this session.");
            return cleanJson(last.plan, last.result);
        }
        default: {
            if ((await git.toplevel(root)) === null) throw new Error("Hooks need a Git repository.");
            return hooks.status(root);
        }
    }
}

/**
 * Opens or copies a result as JSON.
 * @param {"copy" | "open"} mode
 */
export async function jsonCommand(mode) {
    const kind = (
        await vscode.window.showQuickPick(JSON_KINDS, {
            title: `${mode === "copy" ? "Copy" : "Open"} which result as JSON?`,
        })
    )?.label;
    if (!kind) return;
    const root = await pickFolder();
    if (!root) return;
    try {
        const value = await vscode.window.withProgress(
            { location: vscode.ProgressLocation.Notification, title: `Sweepito: building ${kind} JSON` },
            () => jsonFor(kind, root),
        );
        if (mode === "copy") {
            await vscode.env.clipboard.writeText(`${JSON.stringify(value, null, 2)}\n`);
            vscode.window.showInformationMessage(`Sweepito: copied ${kind} as JSON.`);
        } else {
            await showJson(value);
        }
    } catch (error) {
        log(`JSON ${kind} failed: ${errorMessage(error)}`, { error: true });
        vscode.window.showErrorMessage(`Sweepito: ${errorMessage(error)}`);
    }
}
