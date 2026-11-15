import fs from "node:fs";
import path from "node:path";
import { parse } from "smol-toml";
import { parseRisk } from "./models";

export const CONFIG_NAMES = ["sweepito.toml", ".sweepito.toml"];
export const CUSTOM_PROFILE = "custom";

const RULE_KEYS = new Set([
    "id",
    "paths",
    "requires",
    "requires_all",
    "risk",
    "profile",
    "description",
    "allow_untracked",
    "exec",
]);
const PROFILE_KEYS = new Set(["markers", "description"]);
const DEFAULTS_KEYS = new Set(["profiles", "risk"]);
const CLEAN_KEYS = new Set(["enable", "disable", "exclude"]);
const HOOK_KEYS = new Set(["risk", "quiet"]);
const TOP_KEYS = new Set(["defaults", "clean", "hook", "rule", "profile"]);
const RULE_ID = /^[a-z0-9][a-z0-9._-]*$/;

const isTable = (value) => value !== null && typeof value === "object" && !Array.isArray(value);

function norm(table) {
    return Object.fromEntries(Object.entries(table).map(([key, value]) => [key.replace(/-/g, "_"), value]));
}

function table(value, where, allowed) {
    if (!isTable(value)) throw new Error(`[${where}] must be a table.`);
    const normalised = norm(value);
    const unknown = Object.keys(normalised)
        .filter((key) => !allowed.has(key))
        .sort();
    if (unknown.length) throw new Error(`Unknown key(s) in [${where}]: ${unknown.join(", ")}.`);
    return normalised;
}

function strings(value, where) {
    if (!Array.isArray(value) || !value.every((v) => typeof v === "string")) {
        throw new Error(`${where} must be a list of strings.`);
    }
    return [...value];
}

/** Rejects patterns that could escape the project root or negate matches. */
export function validatePattern(pattern, where) {
    const problems = [
        !pattern.trim(),
        /^[!#~]/.test(pattern),
        pattern.includes("\\"),
        /^[A-Za-z]:/.test(pattern),
        pattern.startsWith("//"),
        pattern.split("/").includes(".."),
    ];
    if (problems.some(Boolean)) throw new Error(`Unsafe or invalid path pattern '${pattern}' in ${where}.`);
}

function parseRule(raw, where) {
    const t = table(raw, where, RULE_KEYS);
    if ("exec" in t) {
        throw new Error(`${where}: command rules ('exec') are not supported. Use 'paths' for declarative cleanup.`);
    }
    if ("risk" in t) {
        throw new Error(
            `${where}: custom rules do not take a 'risk' level; they always run. Use 'disable' to switch one off.`,
        );
    }
    if (typeof t.id !== "string" || !RULE_ID.test(t.id)) {
        throw new Error(`${where}: 'id' is required (lowercase letters, digits, . _ -).`);
    }
    const paths = strings(t.paths, `${where} 'paths'`);
    if (paths.length === 0) throw new Error(`${where}: 'paths' must not be empty.`);
    for (const pattern of paths) validatePattern(pattern, `rule '${t.id}'`);
    const allowUntracked = t.allow_untracked ?? false;
    if (typeof allowUntracked !== "boolean") throw new Error(`${where}: 'allow_untracked' must be true or false.`);
    const profile = t.profile ?? CUSTOM_PROFILE;
    if (typeof profile !== "string" || !profile) throw new Error(`${where}: 'profile' must be a non-empty string.`);
    return {
        id: t.id,
        profile,
        paths,
        risk: "custom",
        requires: strings(t.requires ?? [], `${where} 'requires'`),
        requiresAll: strings(t.requires_all ?? [], `${where} 'requires_all'`),
        description: String(t.description ?? ""),
        allowUntracked,
        builtin: false,
    };
}

/** Parses rule tables from a config file or the sweepito.customRules setting. */
export function parseRules(list, label = "[[rule]]") {
    if (!Array.isArray(list)) throw new Error(`'rule' must be an array of tables (${label}).`);
    const rules = list.map((raw, i) => parseRule(raw, `${label} #${i + 1}`));
    const ids = rules.map((r) => r.id);
    if (new Set(ids).size !== ids.length) throw new Error(`Duplicate rule IDs in ${label} entries.`);
    return rules;
}

/** Parses { name: { markers, description } } into { name: { markers, description } }. */
export function parseProfileDefs(value) {
    if (!isTable(value)) throw new Error("[profile] must contain named tables, e.g. [profile.myteam].");
    const defs = {};
    for (const [name, raw] of Object.entries(value)) {
        const t = table(raw, `profile.${name}`, PROFILE_KEYS);
        defs[name] = {
            markers: strings(t.markers ?? [], `[profile.${name}] markers`),
            description: String(t.description ?? ""),
        };
    }
    return defs;
}

/** The nearest config file from `start` up to `stop`, or null. */
export function findConfig(start, stop) {
    let current = path.resolve(start);
    const limit = stop ? path.resolve(stop) : null;
    for (;;) {
        for (const name of CONFIG_NAMES) {
            const candidate = path.join(current, name);
            if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;
        }
        const pyproject = path.join(current, "pyproject.toml");
        if (fs.existsSync(pyproject) && hasPyprojectTable(pyproject)) return pyproject;
        const parent = path.dirname(current);
        if (current === limit || parent === current) return null;
        current = parent;
    }
}

function readToml(file) {
    try {
        return parse(fs.readFileSync(file, "utf8"));
    } catch (error) {
        throw new Error(`Cannot read ${file}: ${error.message}`);
    }
}

function hasPyprojectTable(file) {
    try {
        return isTable(readToml(file).tool) && "sweepito" in readToml(file).tool;
    } catch {
        return false;
    }
}

/** Validated contents of a config file. */
export function loadFileConfig(file) {
    let data = readToml(file);
    if (path.basename(file) === "pyproject.toml") data = data.tool?.sweepito ?? {};
    const unknown = Object.keys(data)
        .filter((key) => !TOP_KEYS.has(key))
        .sort();
    if (unknown.length) throw new Error(`Unknown section(s) in ${path.basename(file)}: ${unknown.join(", ")}.`);

    const cfg = {
        path: file,
        hookRisk: null,
        hookQuiet: false,
        profiles: null,
        risk: null,
        enable: [],
        disable: [],
        exclude: [],
        rules: [],
        profileDefs: {},
    };
    if ("defaults" in data) {
        const t = table(data.defaults, "defaults", DEFAULTS_KEYS);
        if ("profiles" in t) cfg.profiles = strings(t.profiles, "[defaults] profiles");
        if ("risk" in t) cfg.risk = parseRisk(t.risk);
    }
    if ("clean" in data) {
        const t = table(data.clean, "clean", CLEAN_KEYS);
        cfg.enable = strings(t.enable ?? [], "[clean] enable");
        cfg.disable = strings(t.disable ?? [], "[clean] disable");
        cfg.exclude = strings(t.exclude ?? [], "[clean] exclude");
    }
    if ("hook" in data) {
        const t = table(data.hook, "hook", HOOK_KEYS);
        if ("risk" in t) cfg.hookRisk = parseRisk(t.risk);
        const quiet = t.quiet ?? false;
        if (typeof quiet !== "boolean") throw new Error("[hook] quiet must be true or false.");
        cfg.hookQuiet = quiet;
    }
    if ("rule" in data) cfg.rules = parseRules(data.rule);
    if ("profile" in data) cfg.profileDefs = parseProfileDefs(data.profile);
    return cfg;
}

/**
 * Combines the config file with the VS Code settings. A VS Code value wins for `risk` and
 * `profiles` only when it was set explicitly (`undefined` means "not set"); lists are
 * combined, and custom rules and profiles from both sources are added together.
 */
export function mergeConfig(file, vs) {
    file = file ?? { profiles: null, risk: null, enable: [], disable: [], exclude: [], rules: [], profileDefs: {} };
    const exclude = [...file.exclude, ...vs.exclude];
    for (const pattern of exclude) validatePattern(pattern, "exclude");

    const rules = [...file.rules, ...(vs.customRules ? parseRules(vs.customRules, "sweepito.customRules") : [])];
    const ids = rules.map((r) => r.id);
    if (new Set(ids).size !== ids.length)
        throw new Error("Duplicate rule IDs across the config file and sweepito.customRules.");

    const profileDefs = { ...file.profileDefs };
    for (const [name, def] of Object.entries(vs.customProfiles ? parseProfileDefs(vs.customProfiles) : {})) {
        const existing = profileDefs[name];
        profileDefs[name] = existing
            ? { markers: [...existing.markers, ...def.markers], description: def.description || existing.description }
            : def;
    }

    return {
        settings: {
            profiles: vs.profiles ?? file.profiles ?? ["auto"],
            risk: vs.risk ?? file.risk ?? "safe",
            enable: [...file.enable, ...vs.enable],
            disable: [...file.disable, ...vs.disable],
            exclude,
            noGitCheck: vs.noGitCheck,
        },
        custom: { rules, profileDefs },
    };
}
