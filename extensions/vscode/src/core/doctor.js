import { spawn } from "node:child_process";
import fs from "node:fs";
import { prepare, scan } from "./api";
import { cell, plain, table } from "./markdown";
import * as git from "./git";
import * as hooks from "./hooks";
import { detect } from "./precommit";

/** True when `command --version` runs. */
function exists(command) {
    return new Promise((resolve) => {
        const child = spawn(command, ["--version"], { stdio: "ignore" });
        child.on("error", () => resolve(false));
        child.on("close", (code) => resolve(code === 0));
    });
}

const check = (name, ok, detail, required = false) => ({ name, ok, detail, required });

/**
 * Environment diagnostics. `root` is the project folder; `version` is the extension version.
 * A failed required check makes the report unhealthy.
 */
export async function runChecks(root, vs, configFile = "", version = "unknown") {
    const checks = [check("Sweepito extension", true, version), check("Node.js", true, process.versions.node)];
    const gitVersion = await git.version();
    checks.push(check("Git", gitVersion !== null, gitVersion ?? "NOT FOUND", true));
    if (!root) return [...checks, check("Project root", false, "no folder is open", true)];
    if (!fs.existsSync(root)) return [...checks, check("Project root", false, `Not a directory: ${root}`, true)];
    checks.push(check("Project root", true, root));
    if (gitVersion === null) return checks;

    let prepared;
    try {
        prepared = await prepare(root, vs, configFile);
    } catch (error) {
        return [...checks, check("Configuration", false, error.message, true)];
    }
    checks.push(
        check("Configuration", true, prepared.configPath ?? "none (built-in defaults)"),
        check("Risk ceiling", true, prepared.settings.risk),
    );
    const inGit = (await git.toplevel(root)) !== null;
    checks.push(
        check("Git repository", inGit, inGit ? "yes" : "not a Git repository (cleaning needs sweepito.noGitCheck)"),
    );
    if (!inGit) return checks;

    try {
        checks.push(check("Profiles", true, (await scan(root, vs, configFile)).plan.profiles.join(", ")));
    } catch (error) {
        checks.push(check("Profiles", false, error.message));
    }

    const state = await hooks.status(root);
    for (const [stage, installed] of Object.entries(state)) {
        checks.push(check(`${stage} hook`, installed, installed ? "installed" : "not installed"));
        const pinned = installed ? await hooks.pinnedInterpreter(root, stage) : null;
        if (pinned) {
            const usable = hooks.interpreterUsable(pinned);
            checks.push(
                check(
                    `${stage} hook interpreter`,
                    usable,
                    usable ? pinned : `${pinned} is missing; reinstall the hook`,
                ),
            );
        }
    }
    const framework = await detect(root);
    const managedStages = Object.keys(framework.managed).filter((s) => framework.managed[s]);
    const shadowedStages = Object.keys(framework.shadowed).filter((s) => framework.shadowed[s]);
    if (framework.configured || managedStages.length) {
        checks.push(
            check(
                "pre-commit framework",
                shadowedStages.length === 0,
                shadowedStages.length
                    ? `Sweepito's block in the ${shadowedStages.join(", ")} hook never runs because pre-commit's script ends with exec; remove it and use .pre-commit-config.yaml`
                    : framework.configured
                      ? `Sweepito is configured in ${framework.configFile}${managedStages.length ? `; pre-commit manages the ${managedStages.join(", ")} hook` : ""}`
                      : `pre-commit manages the ${managedStages.join(", ")} hook; Sweepito is not in its config`,
            ),
        );
    }
    if (Object.values(state).some(Boolean)) {
        const cli = await exists("sweepito");
        const nodeFallback = (await exists("node")) && (await hooks.scriptInstalled(root));
        checks.push(
            check(
                "Hook runtime",
                cli || nodeFallback,
                cli
                    ? "sweepito command on PATH"
                    : nodeFallback
                      ? "bundled Node script (node on PATH)"
                      : "neither the sweepito command nor node with the hook script is available; the hook does nothing",
            ),
        );
    }
    return checks;
}

/** True when every required check passed. */
export const passed = (checks) => checks.filter((c) => c.required).every((c) => c.ok);

/** Renders the checks as Markdown. */
export function doctorMarkdown(checks) {
    const rows = checks.map((c) => [
        cell(c.name),
        c.ok ? "✅ ok" : c.required ? "❌ failed" : "⚠️ warning",
        plain(c.detail),
    ]);
    return [
        "# Sweepito doctor",
        "",
        passed(checks) ? "**Healthy.** Every required check passed.\n" : "**Not healthy.** A required check failed.\n",
        table("", ["Check", "Status", "Detail"], rows),
    ].join("\n");
}
