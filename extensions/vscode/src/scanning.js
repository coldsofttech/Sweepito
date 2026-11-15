// @ts-check
import * as vscode from "vscode";
import { scan as scanWorkspace } from "./core/api";
import { applyPlan } from "./core/executor";
import { RISK, formatSize } from "./core/models";
import { cleanText, planText } from "./core/text";
import { cleanTerminal, planTerminal } from "./core/terminal";
import { log, toTerminal } from "./output";
import { allCandidates, changed, entries, errorMessage, folders, lastClean, state, states } from "./state";
import { renderStatus, setExpanded } from "./views";
import { configFileSetting, settings } from "./workspace";

const RISKS = Object.keys(RISK);

/**
 * @param {vscode.WorkspaceFolder} folder
 * @param {{ quiet?: boolean }} options
 */
async function scanFolder(folder, { quiet }) {
    const root = folder.uri.fsPath;
    try {
        const result = await scanWorkspace(root, settings(root), configFileSetting(root));
        const plan = { ...result.plan, candidates: result.plan.candidates.map((c) => ({ ...c, folder: root })) };
        states.set(root, {
            name: folder.name,
            root,
            plan,
            error: null,
            descriptions: new Map([...result.registry.rules.values()].map((r) => [r.id, r.description])),
        });
        if (!quiet) {
            log(planText(plan, folder.name));
            toTerminal((c) => planTerminal(plan, folder.name, c));
        }
    } catch (error) {
        states.set(root, { name: folder.name, root, plan: null, error: errorMessage(error), descriptions: new Map() });
        log(`Scan of ${folder.name} failed: ${errorMessage(error)}`, { error: true });
        if (!quiet) vscode.window.showErrorMessage(`Sweepito (${folder.name}): ${errorMessage(error)}`);
    }
}

/** Scans every workspace folder. Resolves with the total number of items found. */
export async function scan({ quiet = false } = {}) {
    if (folders().length === 0 || state.scanning) return 0;
    state.scanning = true;
    renderStatus();
    try {
        for (const root of [...states.keys()]) {
            if (!folders().some((f) => f.uri.fsPath === root)) states.delete(root);
        }
        await vscode.window.withProgress(
            { location: vscode.ProgressLocation.Window, title: "Sweepito: scanning" },
            () => Promise.all(folders().map((f) => scanFolder(f, { quiet }))),
        );
    } finally {
        state.scanning = false;
        const count = allCandidates().length;
        if (count === 0) state.checkFlagged = false;
        renderStatus();
        changed.fire(undefined);
        vscode.commands.executeCommand("setContext", "sweepito.empty", count === 0);
    }
    return allCandidates().length;
}

/** Scans, then says whether anything is left to clean (the CLI's `check`). */
export async function check() {
    if (folders().length === 0) {
        vscode.window.showInformationMessage("Sweepito: open a folder first.");
        return;
    }
    const count = await scan();
    const bytes = entries().reduce((sum, e) => sum + (e.plan?.totalBytes ?? 0), 0);
    state.checkFlagged = count > 0;
    renderStatus();
    if (count === 0) {
        log("Check: clean. Nothing left to clean.");
        vscode.window.showInformationMessage("Sweepito: clean. Nothing left to clean.");
        return;
    }
    log(`Check: ${count} item(s), ${formatSize(bytes)} left to clean.`);
    const answer = await vscode.window.showWarningMessage(
        `Sweepito: ${count} item(s) (${formatSize(bytes)}) left to clean.`,
        "Clean",
        "Show",
    );
    if (answer === "Clean") await clean(allCandidates(), "this workspace");
    else if (answer === "Show") {
        // The view is often already open, so also expand it: that is what "Show" has to make visible.
        await vscode.commands.executeCommand("sweepito.candidates.focus");
        setExpanded(true);
    }
}

/**
 * Confirms, then deletes the given candidates, each from the folder it was found in.
 * @param {{ rule: string, profile: string, risk: string, path: string, isDir: boolean, size: number, folder: string }[]} candidates
 * @param {string} label
 */
export async function clean(candidates, label) {
    if (!vscode.workspace.isTrusted) {
        vscode.window.showWarningMessage("Sweepito cannot clean files in an untrusted workspace.");
        return;
    }
    if (candidates.length === 0) {
        vscode.window.showInformationMessage("Sweepito: nothing to clean.");
        return;
    }
    const size = candidates.reduce((sum, c) => sum + c.size, 0);
    const byFolder = new Map();
    for (const c of candidates) byFolder.set(c.folder, [...(byFolder.get(c.folder) ?? []), c]);
    const withoutGit = [...byFolder.keys()].filter((root) => {
        const plan = states.get(root)?.plan;
        return plan && !plan.inGit;
    });

    if (withoutGit.length) {
        // Always asked, even with confirmBeforeClean off: nothing here is protected by Git.
        const answer = await vscode.window.showWarningMessage(
            `${withoutGit.map((r) => states.get(r)?.name).join(", ")} ${withoutGit.length > 1 ? "are" : "is"} not a Git repository, ` +
                "so Sweepito cannot tell tracked or ignored files apart. " +
                `${candidates.length} item(s) (${formatSize(size)}) will be deleted permanently. Continue?`,
            { modal: true },
            "Delete Anyway",
        );
        if (answer !== "Delete Anyway") return;
    } else if (vscode.workspace.getConfiguration("sweepito").get("confirmBeforeClean", true)) {
        const answer = await vscode.window.showWarningMessage(
            `Delete ${candidates.length} item(s) (${formatSize(size)}) from ${label}? Only git-ignored files are removed.`,
            { modal: true },
            "Delete",
        );
        if (answer !== "Delete") return;
    }

    const total = { removed: [], failed: [], skipped: [], freedBytes: 0 };
    try {
        await vscode.window.withProgress(
            { location: vscode.ProgressLocation.Notification, title: "Sweepito: cleaning" },
            async () => {
                for (const [root, items] of byFolder) {
                    const folderState = states.get(root);
                    if (!folderState?.plan) continue;
                    const result = await applyPlan({ ...folderState.plan, candidates: items });
                    total.removed.push(...result.removed);
                    total.failed.push(...result.failed);
                    total.skipped.push(...result.skipped);
                    total.freedBytes += result.freedBytes;
                    lastClean.set(root, { plan: { ...folderState.plan, candidates: items }, result });
                }
            },
        );
        log(cleanText(total, label), { error: total.failed.length > 0 });
        toTerminal((c) => cleanTerminal(total, c));
        const summary = `Sweepito: freed ${formatSize(total.freedBytes)} (${total.removed.length} removed, ${total.skipped.length} skipped, ${total.failed.length} failed).`;
        if (total.failed.length) vscode.window.showWarningMessage(summary);
        else vscode.window.showInformationMessage(summary);
    } catch (error) {
        log(`Clean failed: ${errorMessage(error)}`, { error: true });
        vscode.window.showErrorMessage(`Sweepito: ${errorMessage(error)}`);
    }
    await scan({ quiet: true });
}

export async function chooseRisk() {
    const first = folders()[0]?.uri.fsPath;
    const current = state.sessionRisk ?? (first ? settings(first).risk : undefined) ?? "safe";
    /** @type {Record<string, string>} */
    const details = {
        safe: "Caches and build output that are always regenerated.",
        configurable: "Larger artifacts that may take time to rebuild.",
        "high-impact": "Items that can cost real work to recreate. Review carefully.",
        custom: "Only your own rules, from the config file or sweepito.customRules.",
    };
    const picked = await vscode.window.showQuickPick(
        RISKS.map((risk) => ({ label: risk, description: risk === current ? "current" : "", detail: details[risk] })),
        { title: "Sweepito risk level for this session" },
    );
    if (!picked) return;
    state.sessionRisk = picked.label;
    await scan();
}
