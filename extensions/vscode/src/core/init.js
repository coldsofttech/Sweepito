import fs from "node:fs";
import path from "node:path";
import template from "./config-template.json";
import { prepare, scan } from "./api";
import { cell, plain, table } from "./markdown";
import * as git from "./git";

export const CONFIG_FILE = "sweepito.toml";

/** The folder `sweepito.toml` belongs in: the Git root, else `root`. */
export async function configRoot(root) {
    return (await git.toplevel(root)) ?? root;
}

/** The path `createConfig` would write for `root`. */
export async function configTarget(root) {
    return path.join(await configRoot(root), CONFIG_FILE);
}

/**
 * Writes a starter sweepito.toml headed by the detected profiles, like `sweepito init`.
 * Refuses to replace an existing file unless `force`. Returns the path.
 */
export async function createConfig(root, vs, configFile = "", { force = false } = {}) {
    const top = await configRoot(root);
    const target = path.join(top, CONFIG_FILE);
    if (fs.existsSync(target) && !force) throw new Error(`${target} already exists. Use force to overwrite.`);
    let detected = [];
    if ((await git.toplevel(top)) !== null) detected = (await scan(top, vs, configFile)).plan.profiles;
    const header = detected.length ? `# Detected profiles: ${detected.join(", ")}\n` : "";
    fs.writeFileSync(target, header + template, { encoding: "utf8" });
    return target;
}

/** Loads and validates the configuration; resolves with a summary or throws the first problem. */
export async function validateConfig(root, vs, configFile = "") {
    const { configPath } = await prepare(root, vs, configFile);
    return configPath;
}

/** The effective configuration as Markdown, like `sweepito config`. */
export async function configMarkdown(root, vs, configFile = "") {
    const { settings, configPath, config, registry } = await prepare(root, vs, configFile);
    const list = (items) => (items.length ? items.map(cell).join(", ") : "none");
    const rows = [
        ["profiles", list(settings.profiles)],
        ["risk", cell(settings.risk)],
        ["enable", list(settings.enable)],
        ["disable", list(settings.disable)],
        ["exclude", list(settings.exclude)],
        ["noGitCheck", cell(settings.noGitCheck)],
    ];
    const custom = [...registry.rules.values()].filter((r) => !r.builtin);
    return [
        "# Sweepito configuration",
        "",
        `- **Config file:** ${configPath ? cell(configPath) : "none (built-in defaults and VS Code settings)"}`,
        "",
        table("Effective settings", ["Setting", "Value"], rows),
        custom.length
            ? table(
                  "Custom rules",
                  ["Rule", "Profile", "Description"],
                  custom.map((r) => [cell(r.id), cell(r.profile), plain(r.description)]),
              )
            : "No custom rules.\n",
        config?.hookRisk ? `Hook risk: ${cell(config.hookRisk)}\n` : "",
    ].join("\n");
}
