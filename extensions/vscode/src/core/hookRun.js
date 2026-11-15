import fs from "node:fs";
import { prepare } from "./api";
import { applyPlan } from "./executor";
import * as git from "./git";
import { formatSize } from "./models";
import { buildPlan } from "./planner";

const NO_OVERRIDES = {
    profiles: undefined,
    risk: undefined,
    exclude: [],
    enable: [],
    disable: [],
    customRules: [],
    customProfiles: {},
    noGitCheck: false,
};

/**
 * What the installed Git hook runs when `sweepito` is not on PATH: `scan` reports, `clean`
 * deletes, both at the [hook] risk of the config file. Returns the exit code.
 * `io` is { out, err } for testing; it defaults to the process streams.
 */
export async function runHook(
    argv,
    cwd,
    io = { out: (t) => process.stdout.write(t), err: (t) => process.stderr.write(t) },
) {
    const action = argv[0];
    if (!["scan", "clean"].includes(action)) {
        io.err(`sweepito: unknown hook action '${action ?? ""}'\n`);
        return 2;
    }
    try {
        const root = fs.realpathSync((await git.toplevel(cwd)) ?? cwd);
        const { settings, registry, config } = await prepare(root, NO_OVERRIDES, "", { hook: true });
        const quiet = argv.includes("--quiet") || Boolean(config?.hookQuiet);
        const plan = await buildPlan(root, settings, registry);
        if (action === "scan") {
            if (!quiet)
                io.out(`Sweepito: ${plan.candidates.length} item(s), ${formatSize(plan.totalBytes)} reclaimable.\n`);
            return 0;
        }
        const result = await applyPlan(plan);
        for (const failure of result.failed) io.err(`sweepito: could not remove ${failure.path}: ${failure.error}\n`);
        if (!quiet) io.out(`Sweepito: freed ${formatSize(result.freedBytes)} (${result.removed.length} removed).\n`);
        return result.failed.length ? 1 : 0;
    } catch (error) {
        io.err(`sweepito: ${error.message}\n`);
        return 1;
    }
}
