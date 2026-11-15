import fs from "node:fs";
import path from "node:path";
import ignore from "ignore";
import * as git from "./git";
import { RISK } from "./models";

const GLOB_CHARS = /[*?[]/;

/** Python's fnmatch.fnmatchcase: `*` also matches `/`. */
export function fnmatch(name, pattern) {
    let re = "";
    for (let i = 0; i < pattern.length; i++) {
        const c = pattern[i];
        if (c === "*") re += ".*";
        else if (c === "?") re += ".";
        else if (c === "[") {
            const end = pattern.indexOf("]", i + 2);
            if (end === -1) re += "\\[";
            else {
                let body = pattern.slice(i + 1, end);
                const negate = body[0] === "!";
                if (negate) body = body.slice(1);
                re += `[${negate ? "^" : ""}${body.replace(/\\/g, "\\\\")}]`;
                i = end;
            }
        } else re += c.replace(/[.+^${}()|\\]/g, "\\$&");
    }
    return new RegExp(`^${re}$`, "s").test(name);
}

export const insideGitDir = (rel) => rel.split("/").includes(".git");

export function confined(root, rel) {
    if (rel.split("/").includes("..")) return false;
    try {
        const rootReal = fs.realpathSync(root);
        const parent = fs.realpathSync(path.dirname(path.join(root, rel)));
        const relative = path.relative(rootReal, parent);
        return !relative.startsWith("..") && !path.isAbsolute(relative);
    } catch {
        return false;
    }
}

/** lstat that reports a missing or unreadable path as null. */
export function lstat(target) {
    try {
        return fs.lstatSync(target);
    } catch {
        return null;
    }
}

/** Symlinks and Windows junctions both report as symbolic links in Node. */
export const isLink = (st) => st.isSymbolicLink();

async function sizeOf(target, isDir) {
    const st = lstat(target);
    if (!st) return 0;
    if (!isDir || isLink(st)) return st.size;
    let total = 0;
    const stack = [target];
    while (stack.length) {
        const current = stack.pop();
        let entries;
        try {
            entries = await fs.promises.readdir(current, { withFileTypes: true });
        } catch {
            continue;
        }
        await Promise.all(
            entries.map(async (entry) => {
                const full = path.join(current, entry.name);
                if (entry.isDirectory() && !entry.isSymbolicLink()) {
                    stack.push(full);
                    return;
                }
                try {
                    total += (await fs.promises.lstat(full)).size;
                } catch {
                    /* vanished while scanning */
                }
            }),
        );
    }
    return total;
}

function findMarker(marker, files) {
    const segments = marker.split("/").length;
    const dirs = new Set();
    for (const name of files) {
        const parts = name.split("/");
        if (parts.length < segments) continue;
        if (fnmatch(parts.slice(-segments).join("/"), marker)) {
            dirs.add(parts.slice(0, -segments).join("/"));
        }
    }
    return dirs;
}

function markerDirs(markers, files, cache) {
    const found = new Set();
    for (const marker of markers) {
        if (!cache.has(marker)) cache.set(marker, findMarker(marker, files));
        for (const dir of cache.get(marker)) found.add(dir);
    }
    return found;
}

function ruleDirs(rule, profileMarkers, files, cache) {
    const anyOf = rule.requires.length ? rule.requires : rule.requiresAll.length ? [] : profileMarkers;
    let dirs = anyOf.length ? markerDirs(anyOf, files, cache) : null;
    for (const marker of rule.requiresAll) {
        if (!cache.has(marker)) cache.set(marker, findMarker(marker, files));
        const found = cache.get(marker);
        dirs = dirs === null ? new Set(found) : new Set([...dirs].filter((d) => found.has(d)));
    }
    return dirs === null ? new Set([""]) : dirs;
}

function splitPatterns(patterns) {
    const literals = [];
    const globs = [];
    for (const pattern of patterns) {
        const anchored = pattern.startsWith("/") || pattern.replace(/\/+$/, "").includes("/");
        if (anchored && !GLOB_CHARS.test(pattern)) {
            literals.push([pattern.replace(/^\/+|\/+$/g, ""), pattern.endsWith("/")]);
        } else globs.push(pattern);
    }
    return [literals, globs];
}

function matchRule(root, rule, dirs, entries) {
    const [literals, globs] = splitPatterns(rule.paths);
    const found = [];
    for (const base of [...dirs].sort()) {
        for (const [literal, needDir] of literals) {
            const rel = base ? `${base}/${literal}` : literal;
            const st = lstat(path.join(root, rel));
            if (!st) continue;
            // A link is never a directory candidate: it is only ever removed as a link.
            const isDir = st.isDirectory() && !isLink(st);
            if (needDir && !isDir) continue;
            found.push([rel, isDir]);
        }
    }
    if (globs.length) {
        const spec = ignore().add(globs);
        for (const entry of entries) {
            const isDir = entry.endsWith("/");
            const parts = entry.replace(/\/$/, "").split("/");
            for (let i = 0; i < parts.length; i++) {
                if (!dirs.has(parts.slice(0, i).join("/"))) continue;
                const rel = parts.slice(i).join("/") + (isDir ? "/" : "");
                if (spec.ignores(rel)) {
                    found.push([parts.join("/"), isDir]);
                    break;
                }
            }
        }
    }
    return found;
}

function excluded(spec, rel, isDir) {
    const parts = rel.split("/");
    return parts.some((_, i) => {
        const last = i === parts.length - 1;
        return spec.ignores(parts.slice(0, i + 1).join("/") + (!last || isDir ? "/" : ""));
    });
}

function activeProfiles(settings, registry, files, cache) {
    const explicit = settings.profiles.filter((p) => p !== "auto");
    const auto = settings.profiles.includes("auto");
    const unknown = explicit.filter((p) => !registry.profiles.has(p));
    if (unknown.length) throw new Error(`Unknown profile(s): ${unknown.sort().join(", ")}.`);
    return [...registry.profiles.values()]
        .filter((profile) =>
            auto
                ? explicit.includes(profile.id) || profile.always || markerDirs(profile.markers, files, cache).size > 0
                : explicit.includes(profile.id),
        )
        .map((profile) => profile.id);
}

function selectRules(settings, registry, active) {
    const disabled = new Set(settings.disable);
    const enabled = new Set(settings.enable);
    const ceiling = RISK[settings.risk];
    const selected = [];
    for (const id of active) {
        for (const rule of registry.profiles.get(id).rules) {
            if (disabled.has(rule.id)) continue;
            if (enabled.has(rule.id) || RISK[rule.risk] <= ceiling) selected.push(rule);
        }
    }
    const covered = new Set(selected.map((r) => r.id));
    for (const id of enabled) {
        if (disabled.has(id) || covered.has(id)) continue;
        const rule = registry.rules.get(id);
        if (!active.includes(rule.profile)) selected.push(rule);
    }
    return selected;
}

/** Without Git every file is a marker source and every entry may be cleaned. */
async function walkInventory(root) {
    const files = [];
    const entries = [];
    const stack = [""];
    while (stack.length) {
        const rel = stack.pop();
        let children;
        try {
            children = await fs.promises.readdir(path.join(root, rel), { withFileTypes: true });
        } catch {
            continue;
        }
        for (const child of children) {
            if (child.name === ".git") continue;
            const name = rel ? `${rel}/${child.name}` : child.name;
            if (child.isDirectory() && !child.isSymbolicLink()) {
                entries.push(`${name}/`);
                stack.push(name);
            } else {
                files.push(name);
                entries.push(name);
            }
        }
    }
    return [files, entries];
}

/**
 * Builds a cleanup plan: detect projects, match rules, apply safety gates.
 * `settings` is { profiles, risk, enable, disable, exclude, noGitCheck }. Outside a Git
 * repository the plan is refused unless `noGitCheck` is set; the git gates are then skipped.
 */
export async function buildPlan(root, settings, registry) {
    root = fs.realpathSync(root);
    const inGit = (await git.toplevel(root)) !== null;
    if (!inGit && !settings.noGitCheck) {
        throw new Error(
            `${root} is not inside a Git repository. Sweepito only removes git-ignored files. ` +
                "Turn on sweepito.noGitCheck to override (high impact).",
        );
    }
    const unknown = [...settings.enable, ...settings.disable].filter((id) => !registry.rules.has(id));
    if (unknown.length) throw new Error(`Unknown rule ID(s): ${[...new Set(unknown)].sort().join(", ")}.`);

    const [files, entries] = inGit
        ? await Promise.all([git.listFiles(root), git.listIgnored(root)])
        : await walkInventory(root);
    const cache = new Map();
    /**
     * @type {{
     *   root: string, inGit: boolean, profiles: string[], totalBytes: number,
     *   candidates: { rule: string, profile: string, risk: string, path: string, isDir: boolean, size: number }[],
     *   skipped: { path: string, rule: string, reason: string }[],
     * }}
     */
    const plan = { root, inGit, profiles: [], candidates: [], skipped: [], totalBytes: 0 };
    plan.profiles = activeProfiles(settings, registry, files, cache);

    const rules = selectRules(settings, registry, plan.profiles);
    // Rules that opt out of the git-ignore check must also see untracked, non-ignored
    // entries, otherwise only anchored paths could ever match them.
    const untracked = inGit && rules.some((r) => r.allowUntracked) ? await git.listUntracked(root) : [];

    const raw = new Map();
    for (const rule of rules) {
        const profile = registry.profiles.get(rule.profile);
        const dirs = ruleDirs(rule, profile.markers, files, cache);
        const source = rule.allowUntracked ? [...entries, ...untracked] : entries;
        for (const [rel, isDir] of matchRule(root, rule, dirs, source)) {
            if (!raw.has(rel)) raw.set(rel, [rule, isDir]);
        }
    }

    const exclude = settings.exclude.length ? ignore().add(settings.exclude) : null;
    const [trackedFiles, trackedDirs] = inGit ? await git.tracked(root) : [new Set(), new Set()];
    const skip = (rel, rule, reason) => plan.skipped.push({ path: rel, rule: rule.id, reason });
    let survivors = [];
    for (const rel of [...raw.keys()].sort()) {
        const [rule, isDir] = raw.get(rel);
        if (insideGitDir(rel)) skip(rel, rule, "inside .git (never cleaned)");
        else if (exclude && excluded(exclude, rel, isDir)) skip(rel, rule, "excluded by configuration");
        else if (!confined(root, rel)) skip(rel, rule, "resolves outside the project root");
        else if (trackedFiles.has(rel) || trackedDirs.has(rel)) skip(rel, rule, "tracked by git");
        else survivors.push([rel, rule, isDir]);
    }

    if (inGit) {
        const needsCheck = survivors.filter(([, rule]) => !rule.allowUntracked).map(([rel]) => rel);
        const ignored = await git.checkIgnored(root, needsCheck);
        survivors = survivors.filter(([rel, rule]) => {
            if (rule.allowUntracked || ignored.has(rel)) return true;
            skip(rel, rule, "not ignored by git");
            return false;
        });
    }

    const keptDirs = [];
    for (let [rel, rule, isDir] of survivors) {
        if (keptDirs.some((d) => rel.startsWith(`${d}/`))) continue; // covered by a parent
        const st = lstat(path.join(root, rel));
        if (isDir && st && isLink(st)) isDir = false;
        if (isDir) keptDirs.push(rel);
        const size = await sizeOf(path.join(root, rel), isDir);
        plan.candidates.push({ rule: rule.id, profile: rule.profile, risk: rule.risk, path: rel, isDir, size });
    }
    plan.totalBytes = plan.candidates.reduce((sum, c) => sum + c.size, 0);
    return plan;
}
