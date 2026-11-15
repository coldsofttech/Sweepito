import { execFileSync, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

// hook-cli.js runs on import and exits the process, so the built script is run as a child.
const builtScript = path.resolve("dist/sweepito-hook.js");
let root;

const git = (...args) => execFileSync("git", ["-C", root, ...args], { stdio: "pipe" });
const write = (rel, text = "x") => {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, text);
};
const hook = (...args) => spawnSync(process.execPath, [builtScript, ...args], { cwd: root, encoding: "utf8" });

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-hookcli-")));
    git("init", "-q");
    write(".gitignore", ".pytest_cache/\n");
    write("pyproject.toml");
    write(".pytest_cache/state", "abc");
    git("add", ".gitignore", "pyproject.toml");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe.skipIf(!fs.existsSync(builtScript))("sweepito-hook.js", () => {
    it("scan reports from the working directory and exits 0 without deleting", () => {
        const result = hook("scan");
        expect(result.status).toBe(0);
        expect(result.stdout).toContain("1 item(s)");
        expect(fs.existsSync(path.join(root, ".pytest_cache"))).toBe(true);
    });

    it("clean deletes and exits 0", () => {
        expect(hook("clean", "--quiet").status).toBe(0);
        expect(fs.existsSync(path.join(root, ".pytest_cache"))).toBe(false);
    });

    it("exits with the code runHook returns for an unknown action", () => {
        expect(hook("bogus").status).toBe(2);
    });

    it("exits 1 and explains a config error", () => {
        write("sweepito.toml", "[nope]\n");
        const result = hook("scan");
        expect(result.status).toBe(1);
        expect(result.stderr).toContain("Unknown section");
    });
});
