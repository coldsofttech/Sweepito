import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { catalog, prepare, report, scan } from "../../../src/core/api";

const vs = { exclude: [], enable: [], disable: [], noGitCheck: false, customRules: [], customProfiles: {} };
let root;

const git = (...args) => execFileSync("git", ["-C", root, ...args], { stdio: "pipe" });
const write = (rel, text = "x") => {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, text);
};

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-api-")));
    git("init", "-q");
    write(".gitignore", ".pytest_cache/\nnode_modules/\n");
    write("pyproject.toml", "[project]\nname = 'x'\n");
    write(".pytest_cache/state", "abc");
    git("add", ".gitignore", "pyproject.toml");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("prepare", () => {
    it("has no config file when none exists", async () => {
        const prepared = await prepare(root, vs);
        expect(prepared.configPath).toBeNull();
        expect(prepared.config).toBeNull();
    });

    it("discovers sweepito.toml and applies its settings", async () => {
        write("sweepito.toml", "[defaults]\nrisk = 'configurable'\n");
        const prepared = await prepare(root, vs);
        expect(prepared.configPath).toBe(path.join(root, "sweepito.toml"));
        expect(prepared.settings.risk).toBe("configurable");
    });

    it("uses an explicit config file instead of discovery", async () => {
        write("sweepito.toml", "[defaults]\nrisk = 'configurable'\n");
        write("other.toml", "[defaults]\nrisk = 'high-impact'\n");
        const prepared = await prepare(root, vs, path.join(root, "other.toml"));
        expect(prepared.configPath).toBe(path.join(root, "other.toml"));
        expect(prepared.settings.risk).toBe("high-impact");
    });

    it("applies the [hook] risk only in hook mode and only when no risk was chosen", async () => {
        write("sweepito.toml", "[hook]\nrisk = 'configurable'\n");
        expect((await prepare(root, vs, "", { hook: true })).settings.risk).toBe("configurable");
        expect((await prepare(root, vs)).settings.risk).not.toBe("configurable");
        expect((await prepare(root, { ...vs, risk: "safe" }, "", { hook: true })).settings.risk).toBe("safe");
    });

    it("reports an invalid config file", async () => {
        write("sweepito.toml", "[nope]\n");
        await expect(prepare(root, vs)).rejects.toThrow(/Unknown section/);
    });
});

describe("catalog", () => {
    it("includes the built-in profiles and custom rules", async () => {
        const registry = await catalog(root, { ...vs, customRules: [{ id: "team.out", paths: ["out/"] }] });
        expect(registry.profiles.has("python")).toBe(true);
        expect(registry.rules.has("team.out")).toBe(true);
    });
});

describe("scan", () => {
    it("plans the ignored caches without deleting them", async () => {
        const result = await scan(root, vs);
        expect(result.plan.candidates.map((c) => c.path)).toEqual([".pytest_cache"]);
        expect(result.configPath).toBeNull();
        expect(result.registry.rules.size).toBeGreaterThan(0);
        expect(fs.existsSync(path.join(root, ".pytest_cache"))).toBe(true);
    });
});

describe("report", () => {
    it("includes high-impact items that a normal scan skips", async () => {
        write("package.json", "{}");
        write("node_modules/x/y.js", "12345");
        const normal = await scan(root, vs);
        expect(normal.plan.candidates.map((c) => c.path)).not.toContain("node_modules");
        const full = await report(root, vs);
        expect(full.root).toBe(root);
        expect(full.risk["high-impact"]).toMatchObject({ count: 1 });
        expect(full.totalBytes).toBeGreaterThanOrEqual(8);
    });
});
