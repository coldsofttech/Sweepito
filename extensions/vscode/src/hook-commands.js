// @ts-check
import path from "node:path";
import * as vscode from "vscode";
import * as hooks from "./core/hooks";
import * as precommit from "./core/precommit";
import { log } from "./output";
import { state } from "./state";
import { requireTrust, withRepo } from "./workspace";

const HOOK_STAGES = [
    {
        label: "post-commit",
        description: "recommended",
        detail: "Cleans automatically after every commit, at the [hook] risk (default: safe).",
    },
    { label: "pre-commit", detail: "Only reports what could be cleaned before each commit; deletes nothing." },
];

const hookScript = () => path.join(state.extensionPath, "dist", "sweepito-hook.js");

export async function installHook() {
    if (!requireTrust()) return;
    await withRepo(async (root) => {
        const stage = (
            await vscode.window.showQuickPick(HOOK_STAGES, { title: "Install the Sweepito Git hook for which stage?" })
        )?.label;
        if (!stage) return;
        await precommit.assertInstallable(root, stage);
        const framework = await precommit.detect(root);
        const answer = await vscode.window.showWarningMessage(
            (framework.configured
                ? `${precommit.CONFIG_FILE} already runs Sweepito, so the hook would run it twice. `
                : "") +
                `Install the ${stage} hook? ` +
                (stage === "post-commit"
                    ? "After every commit in this repository Sweepito will delete the git-ignored files it finds. "
                    : "Before every commit Sweepito will report what could be cleaned. ") +
                "The hook uses the sweepito command if it is on PATH, otherwise a bundled script that needs node on PATH. " +
                "Existing hook content is kept.",
            { modal: true },
            "Install",
        );
        if (answer !== "Install") return;
        const file = await hooks.install(root, stage, hookScript());
        log(`Installed the ${stage} hook: ${file}`);
        vscode.window.showInformationMessage(`Sweepito: installed the ${stage} hook (${file}).`);
    });
}

export async function uninstallHook() {
    if (!requireTrust()) return;
    await withRepo(async (root) => {
        const hookState = await hooks.status(root);
        const installed = HOOK_STAGES.filter((s) => hookState[s.label]);
        if (installed.length === 0) {
            vscode.window.showInformationMessage("Sweepito: no hook is installed.");
            return;
        }
        const picked = await vscode.window.showQuickPick(installed, {
            title: "Remove the Sweepito Git hook for which stage?",
        });
        if (!picked) return;
        const removed = await hooks.uninstall(root, picked.label);
        log(removed ? `Removed the ${picked.label} hook.` : `No ${picked.label} hook installed.`);
        vscode.window.showInformationMessage(
            removed ? `Sweepito: removed the ${picked.label} hook.` : `Sweepito: no ${picked.label} hook installed.`,
        );
    });
}

export async function hookStatus() {
    await withRepo(async (root) => {
        const hookState = await hooks.status(root);
        const framework = await precommit.detect(root);
        const lines = Object.entries(hookState).map(
            ([stage, on]) =>
                `${stage}: ${on ? (framework.shadowed[stage] ? "installed but never runs (pre-commit exec)" : "installed") : framework.managed[stage] && framework.configured ? "managed by pre-commit" : "not installed"}`,
        );
        log(`Hooks - ${lines.join("; ")}`);
        vscode.window.showInformationMessage(`Sweepito hooks - ${lines.join("; ")}`);
    });
}
