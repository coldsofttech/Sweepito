import fs from "node:fs";
import path from "node:path";
import * as git from "./git";

// The markers are shared with the Python command line tool, so each recognises, replaces and
// removes the other's hook.
export const BEGIN = "# >>> sweepito >>>";
export const END = "# <<< sweepito <<<";
export const SCRIPT_NAME = "sweepito-hook.js";
export const STAGES = {
    "post-commit": "clean --hook --non-interactive --quiet",
    "pre-commit": "scan --hook --quiet",
};
const PINNED = /^if \[ -x ('[^\n]*?') \]/m;

/**
 * The hook block: the `sweepito` command if it is on PATH, else the bundled Node script that
 * sits next to the hook, and silence if neither is available.
 */
export function block(stage) {
    const args = STAGES[stage];
    const fail = `|| echo "sweepito: ${stage} hook failed (exit $?)" >&2`;
    return [
        BEGIN,
        "if command -v sweepito >/dev/null 2>&1; then",
        `  sweepito ${args} ${fail}`,
        `elif command -v node >/dev/null 2>&1 && [ -f "$(dirname "$0")/${SCRIPT_NAME}" ]; then`,
        `  node "$(dirname "$0")/${SCRIPT_NAME}" ${args} ${fail}`,
        "fi",
        END,
        "",
    ].join("\n");
}

export async function hookPath(root, stage) {
    if (!(stage in STAGES)) throw new Error(`Unsupported hook stage '${stage}'; use post-commit or pre-commit.`);
    return path.join(await git.hooksDir(root), stage);
}

/** The hook text without the Sweepito block. */
export function strip(text) {
    const start = text.indexOf(BEGIN);
    if (start === -1) return text;
    const head = text.slice(0, start);
    const rest = text.slice(start + BEGIN.length);
    const end = rest.indexOf(END);
    const tail = end === -1 ? "" : rest.slice(end + END.length);
    return `${head.replace(/\n+$/, "")}\n${tail.replace(/^\n+/, "")}`.replace(/^\n+|\n+$/g, "");
}

const read = (file) => (fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "");

/**
 * Adds (or replaces) the Sweepito block, keeping any other content, and copies the Node script
 * next to the hook. `scriptSource` is the bundled sweepito-hook.js. Returns the hook path.
 */
export async function install(root, stage, scriptSource) {
    const file = await hookPath(root, stage);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const base = strip(read(file)) || "#!/bin/sh";
    fs.writeFileSync(file, `${base.replace(/\n+$/, "")}\n\n${block(stage)}`, { encoding: "utf8", mode: 0o755 });
    fs.chmodSync(file, 0o755);
    if (scriptSource) {
        const script = path.join(path.dirname(file), SCRIPT_NAME);
        fs.copyFileSync(scriptSource, script);
        fs.chmodSync(script, 0o755);
    }
    return file;
}

/** Removes the Sweepito block. Returns true if one was removed. */
export async function uninstall(root, stage) {
    const file = await hookPath(root, stage);
    const text = read(file);
    if (!text.includes(BEGIN)) return false;
    const remaining = strip(text);
    if (["", "#!/bin/sh"].includes(remaining.trim())) fs.unlinkSync(file);
    else fs.writeFileSync(file, `${remaining}\n`, "utf8");
    // The Node script is shared by both stages; remove it with the last block.
    if (!Object.values(await status(root)).some(Boolean)) {
        fs.rmSync(path.join(path.dirname(file), SCRIPT_NAME), { force: true });
    }
    return true;
}

/** { stage: installed } for every supported stage. */
export async function status(root) {
    /** @type {Record<string, boolean>} */
    const result = {};
    for (const stage of Object.keys(STAGES)) {
        result[stage] = read(await hookPath(root, stage)).includes(BEGIN);
    }
    return result;
}

/** The interpreter pinned by a hook the Python tool installed, or null. */
export async function pinnedInterpreter(root, stage) {
    const match = PINNED.exec(read(await hookPath(root, stage)));
    return match ? match[1].slice(1, -1).replace(/'\\''/g, "'") : null;
}

/** Whether a Python-pinned interpreter in POSIX form (/c/Python/python.exe on Windows) exists. */
export function interpreterUsable(pinned) {
    const native =
        process.platform === "win32" ? pinned.replace(/^\/([a-z])\//, (_, d) => `${d.toUpperCase()}:/`) : pinned;
    try {
        fs.accessSync(native, fs.constants.X_OK);
        return true;
    } catch {
        return false;
    }
}

/** Where the hook script runs from: whether the Node fallback is in place for any stage. */
export async function scriptInstalled(root) {
    return fs.existsSync(path.join(await git.hooksDir(root), SCRIPT_NAME));
}
