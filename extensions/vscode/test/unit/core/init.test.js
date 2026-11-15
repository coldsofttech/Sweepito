import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { configMarkdown, createConfig, validateConfig } from "../../../src/core/init";

const vs = { exclude: [], enable: [], disable: [], noGitCheck: false, customRules: [], customProfiles: {} };
let root;

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-init-")));
    execFileSync("git", ["-C", root, "init", "-q"]);
    fs.writeFileSync(path.join(root, "pyproject.toml"), "x");
    execFileSync("git", ["-C", root, "add", "."]);
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("createConfig", () => {
    it("writes a starter file headed by the detected profiles that validates", async () => {
        const target = await createConfig(root, vs);
        expect(target).toBe(path.join(root, "sweepito.toml"));
        const text = fs.readFileSync(target, "utf8");
        expect(text).toMatch(/^# Detected profiles: .*python/);
        expect(text).toContain("[defaults]");
        expect(await validateConfig(root, vs)).toBe(target);
    });

    it("refuses to overwrite unless forced", async () => {
        await createConfig(root, vs);
        await expect(createConfig(root, vs)).rejects.toThrow(/already exists/);
        await expect(createConfig(root, vs, "", { force: true })).resolves.toContain("sweepito.toml");
    });
});

describe("validateConfig and configMarkdown", () => {
    it("passes without a config file and reports the problem when one is invalid", async () => {
        expect(await validateConfig(root, vs)).toBeNull();
        fs.writeFileSync(path.join(root, "sweepito.toml"), "[nope]\n");
        await expect(validateConfig(root, vs)).rejects.toThrow(/Unknown section/);
    });

    it("shows the file, effective settings and custom rules", async () => {
        fs.writeFileSync(
            path.join(root, "sweepito.toml"),
            "[defaults]\nrisk = 'configurable'\n[[rule]]\nid = 'team.out'\npaths = ['out/']\ndescription = 'Build output'\n",
        );
        const text = await configMarkdown(root, vs);
        expect(text).toContain(path.join(root, "sweepito.toml"));
        expect(text).toContain("| risk | `configurable` |");
        expect(text).toContain("`team.out`");
    });
});
