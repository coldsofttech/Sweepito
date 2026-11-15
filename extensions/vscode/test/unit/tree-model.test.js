import { describe, expect, it } from "vitest";
import { childrenOf } from "../../src/tree-model";

const candidates = [
    { rule: "python.pycache", profile: "python", risk: "safe", path: "a/__pycache__", isDir: true, size: 1024 },
    { rule: "python.pytest", profile: "python", risk: "safe", path: ".pytest_cache", isDir: true, size: 2048 },
    { rule: "node.cache", profile: "node", risk: "safe", path: ".cache", isDir: true, size: 10 },
];
const entry = (name, items, root = `/w/${name}`) => ({
    name,
    root,
    plan: { candidates: items, totalBytes: items.reduce((s, c) => s + c.size, 0) },
});
const descriptions = new Map([["python.pytest", "pytest cache"]]);

describe("childrenOf", () => {
    it("is empty without folders or with a failed single folder", () => {
        expect(childrenOf([], undefined, descriptions)).toEqual([]);
        expect(childrenOf([{ name: "a", root: "/a", plan: null, error: "boom" }], undefined, descriptions)).toEqual([]);
    });

    it("nests profile, rule and path for a single folder", () => {
        const profiles = childrenOf([entry("app", candidates)], undefined, descriptions);
        expect(profiles.map((p) => p.label)).toEqual(["node", "python"]);
        expect(profiles[1].description).toBe("3.0 KB");
        const rules = childrenOf([], profiles[1], descriptions);
        expect(rules.map((r) => r.label)).toEqual(["python.pycache", "python.pytest"]);
        expect(rules[1].tooltip).toBe("pytest cache");
        const [item] = childrenOf([], rules[0], descriptions);
        expect(item).toMatchObject({ kind: "folder", label: "a/__pycache__", expandable: false });
    });

    it("adds a folder level when there are several folders, and shows failures", () => {
        const entries = [
            entry("app", candidates),
            entry("lib", []),
            { name: "bad", root: "/bad", plan: null, error: "not a repo" },
        ];
        const top = childrenOf(entries, undefined, descriptions);
        expect(top.map((n) => [n.kind, n.label])).toEqual([
            ["workspace", "app"],
            ["workspace", "lib"],
            ["error", "bad"],
        ]);
        expect(top[0]).toMatchObject({ expandable: true, description: "3.0 KB", root: "/w/app" });
        expect(top[1].expandable).toBe(false);
        expect(top[2].tooltip).toBe("not a repo");
        expect(childrenOf(entries, top[0], descriptions).map((p) => p.label)).toEqual(["node", "python"]);
    });
});
