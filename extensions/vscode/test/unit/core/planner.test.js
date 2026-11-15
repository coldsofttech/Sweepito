import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { applyPlan } from "../../../src/core/executor";
import { buildPlan, fnmatch } from "../../../src/core/planner";
import { buildRegistry } from "../../../src/core/registry";

const registry = buildRegistry();
const settings = { profiles: ["auto"], risk: "safe", enable: [], disable: [], exclude: [] };
let root;

const git = (...args) => execFileSync("git", ["-C", root, ...args], { stdio: "pipe" });
const write = (rel, text = "x") => {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, text);
};

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-")));
    git("init", "-q");
    write(".gitignore", "__pycache__/\n.pytest_cache/\nnode_modules/\n");
    write("pyproject.toml");
    write("pkg/__pycache__/a.pyc", "12345");
    write(".pytest_cache/state", "abc");
    write("src/keep.py");
    git("add", ".gitignore", "pyproject.toml", "src/keep.py");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("buildPlan", () => {
    it("finds ignored caches of detected profiles", async () => {
        const plan = await buildPlan(root, settings, registry);
        expect(plan.profiles).toContain("python");
        expect(plan.candidates.map((c) => c.path).sort()).toEqual([".pytest_cache", "pkg/__pycache__"]);
        expect(plan.totalBytes).toBe(8);
    });

    it("never offers tracked files", async () => {
        git("add", "-f", "pkg/__pycache__/a.pyc");
        const plan = await buildPlan(root, settings, registry);
        expect(plan.candidates.map((c) => c.path)).not.toContain("pkg/__pycache__");
    });

    it("honours exclude patterns and disabled rules", async () => {
        const plan = await buildPlan(root, { ...settings, exclude: ["pkg/"], disable: ["python.pytest"] }, registry);
        expect(plan.candidates).toEqual([]);
    });

    it("rejects unknown rule IDs and non-repositories", async () => {
        await expect(buildPlan(root, { ...settings, enable: ["nope.rule"] }, registry)).rejects.toThrow(/Unknown rule/);
        const outside = fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-nogit-"));
        await expect(buildPlan(outside, settings, registry)).rejects.toThrow(/not inside a Git repository/);
        fs.rmSync(outside, { recursive: true, force: true });
    });
});

describe("noGitCheck", () => {
    it("scans and cleans a folder that is not a repository", async () => {
        const plain = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-plain-")));
        try {
            fs.writeFileSync(path.join(plain, "pyproject.toml"), "x");
            fs.mkdirSync(path.join(plain, ".pytest_cache"));
            fs.writeFileSync(path.join(plain, ".pytest_cache", "state"), "abc");
            const plan = await buildPlan(plain, { ...settings, noGitCheck: true }, registry);
            expect(plan.inGit).toBe(false);
            expect(plan.candidates.map((c) => c.path)).toEqual([".pytest_cache"]);
            const result = await applyPlan(plan);
            expect(result.freedBytes).toBe(3);
            expect(fs.existsSync(path.join(plain, ".pytest_cache"))).toBe(false);
        } finally {
            fs.rmSync(plain, { recursive: true, force: true });
        }
    });
});

describe("helpers", () => {
    it("matches markers like Python's fnmatch", () => {
        expect(fnmatch("requirements-dev.txt", "requirements*.txt")).toBe(true);
        expect(fnmatch("setup.py", "setup.cfg")).toBe(false);
    });
});
