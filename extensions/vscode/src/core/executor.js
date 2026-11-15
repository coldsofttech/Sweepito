import fs from "node:fs";
import path from "node:path";
import * as git from "./git";
import { insideGitDir, confined, isLink, lstat } from "./planner";

/** Removes one file or link; a directory link goes without touching its target. */
async function unlink(target) {
    const st = lstat(target);
    if (!st) return [0, []];
    try {
        if (isLink(st) && process.platform === "win32") {
            try {
                await fs.promises.rmdir(target); // a junction or directory symlink, not its contents
            } catch {
                await fs.promises.unlink(target);
            }
        } else {
            await fs.promises.unlink(target);
        }
    } catch (error) {
        if (error.code === "ENOENT") return [0, []];
        return [0, [[target, error.message]]];
    }
    return [st.size, []];
}

/** Removes a file, link or directory tree. Links are never traversed. */
async function remove(target) {
    const st = lstat(target);
    if (!st) return [0, []];
    if (isLink(st) || !st.isDirectory()) return unlink(target);

    let freed = 0;
    const errors = [];
    const stack = [target];
    const order = [];
    while (stack.length) {
        const current = stack.pop();
        order.push(current);
        let entries;
        try {
            entries = await fs.promises.readdir(current, { withFileTypes: true });
        } catch (error) {
            errors.push([current, error.message]);
            continue;
        }
        for (const entry of entries) {
            const full = path.join(current, entry.name);
            if (entry.isDirectory() && !entry.isSymbolicLink()) {
                stack.push(full);
            } else {
                const [size, errs] = await unlink(full);
                freed += size;
                errors.push(...errs);
            }
        }
    }
    for (const directory of order.reverse()) {
        try {
            await fs.promises.rmdir(directory);
        } catch (error) {
            errors.push([directory, error.message]);
        }
    }
    return [freed, errors];
}

/** Deletes planned candidates. Failures are reported, never worked around. */
export async function applyPlan(plan) {
    const result = { removed: [], failed: [], skipped: [], freedBytes: 0 };
    // Re-read tracked state right before deleting, in case it changed since planning.
    const [trackedFiles, trackedDirs] = plan.inGit ? await git.tracked(plan.root) : [new Set(), new Set()];
    for (const cand of plan.candidates) {
        const skip = (reason) => result.skipped.push({ path: cand.path, rule: cand.rule, reason });
        if (trackedFiles.has(cand.path) || trackedDirs.has(cand.path)) skip("tracked by git");
        else if (insideGitDir(cand.path)) skip("inside .git (never cleaned)");
        else if (!confined(plan.root, cand.path)) skip("resolves outside the project root");
        else {
            const [freed, errors] = await remove(path.join(plan.root, cand.path));
            result.freedBytes += freed;
            if (errors.length) result.failed.push(...errors.map(([p, error]) => ({ path: p, error })));
            else result.removed.push(cand);
        }
    }
    return result;
}
