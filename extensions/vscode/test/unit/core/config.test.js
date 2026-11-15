import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { scan } from "../../../src/core/api";
import { findConfig, loadFileConfig, mergeConfig, parseRules, validatePattern } from "../../../src/core/config";
import { applyPlan } from "../../../src/core/executor";

const vs = { exclude: [], enable: [], disable: [], noGitCheck: false };
let root;

const git = (...args) => execFileSync("git", ["-C", root, ...args], { stdio: "pipe" });
const write = (rel, text = "x") => {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, text);
};

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-cfg-")));
    git("init", "-q");
    write(".gitignore", "out/\n");
    git("add", ".gitignore");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("validation", () => {
    it("rejects unsafe patterns", () => {
        for (const bad of ["", "!keep", "../x", "a\\b", "C:/x", "//share", "~/x", "#c"]) {
            expect(() => validatePattern(bad, "test")).toThrow(/Unsafe/);
        }
        expect(() => validatePattern("out/", "test")).not.toThrow();
    });

    it("rejects bad rules", () => {
        expect(() => parseRules([{ id: "Bad ID", paths: ["x"] }])).toThrow(/'id' is required/);
        expect(() => parseRules([{ id: "a", paths: [] }])).toThrow(/must not be empty/);
        expect(() => parseRules([{ id: "a", paths: ["x"], risk: "safe" }])).toThrow(/do not take a 'risk'/);
        expect(() => parseRules([{ id: "a", paths: ["x"], exec: "rm" }])).toThrow(/exec/);
        expect(() =>
            parseRules([
                { id: "a", paths: ["x"] },
                { id: "a", paths: ["y"] },
            ]),
        ).toThrow(/Duplicate/);
    });
});

describe("config files", () => {
    it("finds sweepito.toml or the pyproject table", () => {
        write("pyproject.toml", "[project]\nname='x'\n");
        expect(findConfig(root, root)).toBeNull();
        write("pyproject.toml", "[tool.sweepito.defaults]\nrisk = 'configurable'\n");
        expect(findConfig(root, root)).toBe(path.join(root, "pyproject.toml"));
        expect(loadFileConfig(findConfig(root, root)).risk).toBe("configurable");
    });

    it("rejects unknown sections", () => {
        write("sweepito.toml", "[bogus]\n");
        expect(() => loadFileConfig(path.join(root, "sweepito.toml"))).toThrow(/Unknown section/);
    });

    it("explicit VS Code values beat the file; lists are combined", () => {
        write("sweepito.toml", "[defaults]\nrisk = 'configurable'\n[clean]\nenable = ['a']\n");
        const file = loadFileConfig(path.join(root, "sweepito.toml"));
        expect(mergeConfig(file, { ...vs }).settings.risk).toBe("configurable");
        expect(mergeConfig(file, { ...vs, risk: "safe", enable: ["b"] }).settings).toMatchObject({
            risk: "safe",
            enable: ["a", "b"],
        });
    });
});

describe("custom rules", () => {
    it("run at the custom level and clean ignored output", async () => {
        write("out/a.bin", "12345");
        write("keep.txt");
        git("add", "keep.txt");
        const customRules = [{ id: "team.out", paths: ["out/"], description: "Build output" }];
        const { plan } = await scan(root, { ...vs, customRules });
        expect(plan.profiles).toContain("custom");
        expect(plan.candidates).toMatchObject([{ rule: "team.out", risk: "custom", path: "out", size: 5 }]);
        expect(plan.candidates).toHaveLength(1);
    });

    it("only run alone at risk custom, and can be disabled", async () => {
        write("out/a.bin");
        write("package.json", "{}");
        write("node_modules/x/y.js", "x");
        git("add", "package.json");
        const customRules = [{ id: "team.out", paths: ["out/"] }];
        const alone = await scan(root, { ...vs, customRules, risk: "custom" });
        expect(alone.plan.candidates.map((c) => c.rule)).toEqual(["team.out"]);
        const off = await scan(root, { ...vs, customRules, disable: ["team.out"] });
        expect(off.plan.candidates.map((c) => c.rule)).not.toContain("team.out");
    });

    it("custom profiles switch on from their markers", async () => {
        write("out/a.bin");
        write("Teamfile");
        git("add", "Teamfile");
        const customRules = [{ id: "team.out", profile: "myteam", paths: ["out/"] }];
        const customProfiles = { myteam: { markers: ["Teamfile"], description: "Team" } };
        const { plan } = await scan(root, { ...vs, customRules, customProfiles });
        expect(plan.profiles).toContain("myteam");
        expect(plan.candidates.map((c) => c.path)).toEqual(["out"]);
    });

    it("allow_untracked matches files git does not ignore, others do not", async () => {
        write("scratch/tmp.log", "abc");
        const safe = await scan(root, { ...vs, customRules: [{ id: "t.scratch", paths: ["scratch/"] }] });
        expect(safe.plan.candidates).toEqual([]);
        const open = await scan(root, {
            ...vs,
            customRules: [{ id: "t.scratch", paths: ["scratch/"], allow_untracked: true }],
        });
        expect(open.plan.candidates.map((c) => c.path)).toEqual(["scratch"]);
        const result = await applyPlan(open.plan);
        expect(result.freedBytes).toBe(3);
        expect(fs.existsSync(path.join(root, "scratch"))).toBe(false);
    });

    it("never offers tracked files even with allow_untracked", async () => {
        write("scratch/tmp.log");
        git("add", "scratch/tmp.log");
        const { plan } = await scan(root, {
            ...vs,
            customRules: [{ id: "t.scratch", paths: ["scratch/"], allow_untracked: true }],
        });
        expect(plan.candidates).toEqual([]);
    });

    it("rejects an ID that clashes with a built-in rule", async () => {
        await expect(scan(root, { ...vs, customRules: [{ id: "python.pytest", paths: ["x/"] }] })).rejects.toThrow(
            /Duplicate rule ID/,
        );
    });
});
