import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import * as git from "../../../src/core/git";

let root;

const run = (...args) => execFileSync("git", ["-C", root, ...args], { stdio: "pipe" });
const write = (rel, text = "x") => {
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, text);
};

beforeEach(() => {
    root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-git-")));
    run("init", "-q");
    write(".gitignore", "cache/\n*.log\n");
    write("src/a.py");
    write("src/pkg/b.py");
    run("add", ".gitignore", "src");
    write("cache/data", "x");
    write("debug.log");
    write("notes/todo.txt");
});

afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

describe("toplevel and version", () => {
    it("finds the repository root from a subfolder", async () => {
        expect(await git.toplevel(path.join(root, "src", "pkg"))).toBe(root.replaceAll("\\", "/"));
    });

    it("is null outside a repository", async () => {
        const outside = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sweepito-nogit-")));
        try {
            expect(await git.toplevel(outside)).toBeNull();
        } finally {
            fs.rmSync(outside, { recursive: true, force: true });
        }
    });

    it("reports the git version", async () => {
        expect(await git.version()).toMatch(/^git version/);
    });
});

describe("hooksDir", () => {
    it("is the absolute hooks folder of the repository", async () => {
        expect(path.resolve(await git.hooksDir(root))).toBe(path.join(root, ".git", "hooks"));
    });
});

describe("listing files", () => {
    it("listFiles returns tracked and untracked, not ignored", async () => {
        const files = (await git.listFiles(root)).sort();
        expect(files).toEqual([".gitignore", "notes/todo.txt", "src/a.py", "src/pkg/b.py"]);
    });

    it("listIgnored returns ignored entries, with directories ending in a slash", async () => {
        expect((await git.listIgnored(root)).sort()).toEqual(["cache/", "debug.log"]);
    });

    it("listUntracked returns untracked files and their parent directories", async () => {
        expect(await git.listUntracked(root)).toEqual(["notes/todo.txt", "notes/"]);
    });

    it("tracked returns the tracked files and every directory above them", async () => {
        const [files, dirs] = await git.tracked(root);
        expect([...files].sort()).toEqual([".gitignore", "src/a.py", "src/pkg/b.py"]);
        expect([...dirs].sort()).toEqual(["src", "src/pkg"]);
    });
});

describe("checkIgnored", () => {
    it("returns only the ignored subset", async () => {
        const ignored = await git.checkIgnored(root, ["cache", "debug.log", "src/a.py"]);
        expect([...ignored].sort()).toEqual(["cache", "debug.log"]);
    });

    it("returns an empty set for no paths", async () => {
        expect((await git.checkIgnored(root, [])).size).toBe(0);
    });
});
