import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { applyPlan } from "../../../src/core/executor";
import { buildPlan } from "../../../src/core/planner";
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
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-exec-")));
    git("init", "-q");
    write(".gitignore", "__pycache__/\n.pytest_cache/\nnode_modules/\n");
    write("pyproject.toml");
    write("pkg/__pycache__/a.pyc", "12345");
    write(".pytest_cache/state", "abc");
    write("src/keep.py");
    git("add", ".gitignore", "pyproject.toml", "src/keep.py");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("applyPlan", () => {
    it("deletes candidates and reports freed bytes", async () => {
        const plan = await buildPlan(root, settings, registry);
        const result = await applyPlan(plan);
        expect(result.failed).toEqual([]);
        expect(result.freedBytes).toBe(8);
        expect(fs.existsSync(path.join(root, "pkg/__pycache__"))).toBe(false);
        expect(fs.existsSync(path.join(root, "src/keep.py"))).toBe(true);
    });

    it("skips anything that became tracked after planning", async () => {
        const plan = await buildPlan(root, settings, registry);
        git("add", "-f", ".pytest_cache/state");
        const result = await applyPlan(plan);
        expect(result.skipped.map((s) => s.path)).toContain(".pytest_cache");
        expect(fs.existsSync(path.join(root, ".pytest_cache/state"))).toBe(true);
    });
});
