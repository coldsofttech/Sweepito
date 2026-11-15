import { findConfig, loadFileConfig, mergeConfig } from "./config";
import * as git from "./git";
import { buildPlan } from "./planner";
import { buildRegistry } from "./registry";
import { buildReport } from "./report";

/**
 * Resolves the effective settings and registry for `root`. `vs` holds the VS Code settings
 * (`risk` and `profiles` are undefined unless set explicitly); `configFile` overrides discovery.
 */
export async function prepare(root, vs, configFile = "", { hook = false } = {}) {
    let file = null;
    if (configFile) {
        file = loadFileConfig(configFile);
    } else {
        const top = await git.toplevel(root);
        const found = findConfig(root, top ?? root);
        if (found) file = loadFileConfig(found);
    }
    // Like the CLI's --hook: the [hook] risk applies unless a risk was chosen explicitly.
    const effective = hook && file?.hookRisk && !vs.risk ? { ...vs, risk: file.hookRisk } : vs;
    const { settings, custom } = mergeConfig(file, effective);
    return { settings, registry: buildRegistry(undefined, custom), configPath: file?.path ?? null, config: file };
}

/** The registry (built-in plus custom profiles and rules) for browsing. */
export async function catalog(root, vs, configFile = "") {
    return (await prepare(root, vs, configFile)).registry;
}

/** Plans everything at the highest risk level without deleting: the data for a report. */
export async function report(root, vs, configFile = "") {
    const { settings, registry } = await prepare(root, vs, configFile);
    const plan = await buildPlan(root, { ...settings, risk: "high-impact" }, registry);
    return buildReport(plan);
}

/** Prepares and scans in one step. */
export async function scan(root, vs, configFile = "") {
    const { settings, registry, configPath } = await prepare(root, vs, configFile);
    return { plan: await buildPlan(root, settings, registry), registry, configPath };
}
