import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { install } from "../../../src/core/hooks";
import { runHook } from "../../../src/core/hookRun";

const builtScript = path.resolve("dist/sweepito-hook.js");
let root;

const git = (...args) => execFileSync("git", ["-C", root, ...args], { stdio: "pipe" }).toString();
const write = (rel, text = "x") => {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, text);
};
const io = () => {
    const log = { out: "", err: "" };
    return { log, io: { out: (t) => (log.out += t), err: (t) => (log.err += t) } };
};

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-hookrun-")));
    git("init", "-q");
    git("config", "user.email", "t@example.com");
    git("config", "user.name", "t");
    write(".gitignore", ".pytest_cache/\n");
    write("pyproject.toml");
    git("add", ".");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("runHook", () => {
    it("scan reports without deleting, clean deletes", async () => {
        write(".pytest_cache/state", "abc");
        const scan = io();
        expect(await runHook(["scan"], root, scan.io)).toBe(0);
        expect(scan.log.out).toContain("1 item(s)");
        expect(fs.existsSync(path.join(root, ".pytest_cache"))).toBe(true);

        const quiet = io();
        expect(await runHook(["clean", "--quiet"], root, quiet.io)).toBe(0);
        expect(quiet.log.out).toBe("");
        expect(fs.existsSync(path.join(root, ".pytest_cache"))).toBe(false);
    });

    it("uses the [hook] risk and quiet settings of the config file", async () => {
        write("package.json", "{}");
        write(".gitignore", ".pytest_cache/\ndist/\n");
        write("dist/out.js", "x");
        write(".pytest_cache/state", "abc");
        write("sweepito.toml", "[hook]\nrisk = 'custom'\nquiet = true\n");
        const run = io();
        expect(await runHook(["clean"], root, run.io)).toBe(0);
        expect(run.log.out).toBe("");
        expect(fs.existsSync(path.join(root, ".pytest_cache"))).toBe(true); // safe rules are above 'custom'
    });

    it("rejects unknown actions and reports config errors", async () => {
        const bad = io();
        expect(await runHook(["bogus"], root, bad.io)).toBe(2);
        write("sweepito.toml", "[nope]\n");
        const broken = io();
        expect(await runHook(["scan"], root, broken.io)).toBe(1);
        expect(broken.log.err).toContain("Unknown section");
    });
});

describe.skipIf(!fs.existsSync(builtScript))("installed hook", () => {
    it("cleans after a real commit through the bundled script", async () => {
        await install(root, "post-commit", builtScript);
        write(".pytest_cache/state", "abc");
        write("file.txt");
        git("add", "file.txt");
        // Keep sweepito itself off PATH so the Node fallback is the one that runs.
        const env = {
            ...process.env,
            PATH: process.env.PATH.split(path.delimiter)
                .filter((p) => !fs.existsSync(path.join(p, "sweepito")))
                .join(path.delimiter),
        };
        execFileSync("git", ["-C", root, "commit", "-q", "-m", "x"], { env, stdio: "pipe" });
        expect(fs.existsSync(path.join(root, ".pytest_cache"))).toBe(false);
    });
});
