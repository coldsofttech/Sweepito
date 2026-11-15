import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { BEGIN, END, SCRIPT_NAME, install, status, strip, uninstall } from "../../../src/core/hooks";

let root;

const git = (...args) => execFileSync("git", ["-C", root, ...args], { stdio: "pipe" }).toString();
const write = (rel, text = "x") => {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, text);
};
const hook = (stage) => path.join(root, ".git", "hooks", stage);

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-hook-")));
    git("init", "-q");
    git("config", "user.email", "t@example.com");
    git("config", "user.name", "t");
    write(".gitignore", ".pytest_cache/\n");
    write("pyproject.toml");
    git("add", ".");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("install, status and uninstall", () => {
    it("adds a marked block and the Node script, and removes them again", async () => {
        const script = path.join(root, "fake-hook.js");
        fs.writeFileSync(script, "// script");
        await install(root, "post-commit", script);
        const text = fs.readFileSync(hook("post-commit"), "utf8");
        expect(text.startsWith("#!/bin/sh")).toBe(true);
        expect(text).toContain(BEGIN);
        expect(text).toContain("clean --hook --non-interactive --quiet");
        expect(fs.existsSync(path.join(root, ".git", "hooks", SCRIPT_NAME))).toBe(true);
        expect(await status(root)).toEqual({ "post-commit": true, "pre-commit": false });

        expect(await uninstall(root, "post-commit")).toBe(true);
        expect(fs.existsSync(hook("post-commit"))).toBe(false);
        expect(fs.existsSync(path.join(root, ".git", "hooks", SCRIPT_NAME))).toBe(false);
        expect(await uninstall(root, "post-commit")).toBe(false);
    });

    it("keeps existing hook content and replaces its own block when reinstalled", async () => {
        fs.mkdirSync(path.dirname(hook("pre-commit")), { recursive: true });
        fs.writeFileSync(hook("pre-commit"), "#!/bin/sh\necho mine\n");
        await install(root, "pre-commit");
        await install(root, "pre-commit");
        const text = fs.readFileSync(hook("pre-commit"), "utf8");
        expect(text).toContain("echo mine");
        expect(text.split(BEGIN)).toHaveLength(2);
        await uninstall(root, "pre-commit");
        expect(fs.readFileSync(hook("pre-commit"), "utf8")).toBe("#!/bin/sh\necho mine\n");
    });

    it("keeps the shared script while another stage still uses it", async () => {
        const script = path.join(root, "fake-hook.js");
        fs.writeFileSync(script, "// script");
        await install(root, "post-commit", script);
        await install(root, "pre-commit", script);
        await uninstall(root, "post-commit");
        expect(fs.existsSync(path.join(root, ".git", "hooks", SCRIPT_NAME))).toBe(true);
        await uninstall(root, "pre-commit");
        expect(fs.existsSync(path.join(root, ".git", "hooks", SCRIPT_NAME))).toBe(false);
    });

    it("recognises and removes a block written by the Python tool", async () => {
        const python = `#!/bin/sh\n\n${BEGIN}\nif [ -x '/usr/bin/python3' ]; then\n  true\nfi\n${END}\n`;
        fs.mkdirSync(path.dirname(hook("post-commit")), { recursive: true });
        fs.writeFileSync(hook("post-commit"), python);
        expect((await status(root))["post-commit"]).toBe(true);
        expect(strip(python)).toBe("#!/bin/sh");
        expect(await uninstall(root, "post-commit")).toBe(true);
        expect(fs.existsSync(hook("post-commit"))).toBe(false);
    });

    it("rejects an unknown stage", async () => {
        await expect(install(root, "pre-push")).rejects.toThrow(/Unsupported hook stage/);
    });
});
