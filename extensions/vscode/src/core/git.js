import { spawn } from "node:child_process";
import path from "node:path";

const ENV = { ...process.env, GIT_OPTIONAL_LOCKS: "0" };

/** Runs git in `root`; resolves with { code, stdout }. Paths are posix, relative to root. */
function run(root, args, { input, ok = [0] } = {}) {
    return new Promise((resolve, reject) => {
        const child = spawn("git", ["-C", root, ...args], { env: ENV });
        const out = [];
        const err = [];
        child.stdout.on("data", (chunk) => out.push(chunk));
        child.stderr.on("data", (chunk) => err.push(chunk));
        child.on("error", (error) => {
            reject(error.code === "ENOENT" ? new Error("The git executable was not found on PATH.") : error);
        });
        child.on("close", (code) => {
            const stdout = Buffer.concat(out).toString("utf8");
            if (!ok.includes(code)) {
                reject(new Error(`git ${args[0]} failed: ${Buffer.concat(err).toString("utf8").trim()}`));
            } else {
                resolve({ code, stdout });
            }
        });
        child.stdin.on("error", () => {});
        child.stdin.end(input);
    });
}

const split = (output) => output.split("\0").filter(Boolean);

function parentDirs(files) {
    const dirs = new Set();
    for (const name of files) {
        let parent = name.slice(0, Math.max(name.lastIndexOf("/"), 0));
        while (parent && !dirs.has(parent)) {
            dirs.add(parent);
            parent = parent.slice(0, Math.max(parent.lastIndexOf("/"), 0));
        }
    }
    return dirs;
}

/** The work tree root containing `dir`, or null if it is not in a repository. */
export async function toplevel(dir) {
    try {
        const { code, stdout } = await run(dir, ["rev-parse", "--show-toplevel"], { ok: [0, 128] });
        return code === 0 ? stdout.trim() : null;
    } catch (error) {
        if (/not found on PATH/.test(error.message)) throw error;
        return null;
    }
}

/** The git version line, or null when git is not installed. */
export async function version() {
    try {
        const { stdout } = await run(process.cwd(), ["--version"]);
        return stdout.trim() || null;
    } catch {
        return null;
    }
}

/** The hooks directory of the repository containing `root`, as an absolute path. */
export async function hooksDir(root) {
    const { stdout } = await run(root, ["rev-parse", "--git-path", "hooks"]);
    const dir = stdout.trim();
    return path.isAbsolute(dir) ? dir : path.resolve(root, dir);
}

/** Tracked files plus untracked files that are not ignored. */
export async function listFiles(root) {
    const { stdout } = await run(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"]);
    return split(stdout);
}

/** Ignored, untracked entries. Fully ignored directories end with a slash. */
export async function listIgnored(root) {
    const { stdout } = await run(root, [
        "ls-files",
        "-z",
        "--others",
        "--ignored",
        "--exclude-standard",
        "--directory",
    ]);
    return split(stdout);
}

/**
 * Untracked, non-ignored files plus every directory above them (trailing slash). Files are
 * listed individually so patterns can match inside an untracked directory.
 */
export async function listUntracked(root) {
    const { stdout } = await run(root, ["ls-files", "-z", "--others", "--exclude-standard"]);
    const files = split(stdout);
    return [...files, ...[...parentDirs(files)].sort().map((d) => `${d}/`)];
}

/** Returns [tracked files, every directory containing a tracked file]. */
export async function tracked(root) {
    const { stdout } = await run(root, ["ls-files", "-z", "--cached"]);
    const files = new Set(split(stdout));
    return [files, parentDirs(files)];
}

/** The subset of `paths` that git ignores. */
export async function checkIgnored(root, paths) {
    if (paths.length === 0) return new Set();
    const input = paths.map((p) => `${p}\0`).join("");
    const { stdout } = await run(root, ["check-ignore", "-z", "--stdin"], { input, ok: [0, 1] });
    return new Set(split(stdout));
}
