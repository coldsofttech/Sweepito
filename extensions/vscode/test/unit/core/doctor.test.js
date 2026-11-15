import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { doctorMarkdown, passed, runChecks } from "../../../src/core/doctor";
import { install } from "../../../src/core/hooks";

const builtScript = path.resolve("dist/sweepito-hook.js");
const vs = { exclude: [], enable: [], disable: [], noGitCheck: false, customRules: [], customProfiles: {} };
let root;

const git = (...args) => execFileSync("git", ["-C", root, ...args], { stdio: "pipe" }).toString();
const write = (rel, text = "x") => {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, text);
};

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-doctor-")));
    git("init", "-q");
    git("config", "user.email", "t@example.com");
    git("config", "user.name", "t");
    write(".gitignore", ".pytest_cache/\n");
    write("pyproject.toml");
    git("add", ".");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("doctor", () => {
    it("is healthy in a repository and lists hook state", async () => {
        await install(root, "post-commit", builtScript);
        const checks = await runChecks(root, vs, "", "9.9.9");
        const names = checks.map((c) => c.name);
        expect(names).toEqual(
            expect.arrayContaining([
                "Git",
                "Project root",
                "Configuration",
                "Profiles",
                "post-commit hook",
                "pre-commit hook",
            ]),
        );
        expect(checks.find((c) => c.name === "post-commit hook").ok).toBe(true);
        expect(checks.find((c) => c.name === "pre-commit hook").ok).toBe(false);
        expect(passed(checks)).toBe(true);
        expect(doctorMarkdown(checks)).toContain("**Healthy.**");
    });

    it("fails on a bad config and stops there", async () => {
        write("sweepito.toml", "[nope]\n");
        const checks = await runChecks(root, vs);
        expect(passed(checks)).toBe(false);
        expect(checks.at(-1)).toMatchObject({ name: "Configuration", ok: false, required: true });
        expect(doctorMarkdown(checks)).toContain("**Not healthy.**");
    });

    it("flags a folder that is not a repository without failing", async () => {
        const plain = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-plain-")));
        try {
            const checks = await runChecks(plain, vs);
            expect(checks.find((c) => c.name === "Git repository")).toMatchObject({ ok: false, required: false });
            expect(passed(checks)).toBe(true);
        } finally {
            fs.rmSync(plain, { recursive: true, force: true });
        }
    });
});
