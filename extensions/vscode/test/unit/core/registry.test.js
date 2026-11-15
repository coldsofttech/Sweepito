import { describe, expect, it } from "vitest";
import { buildRegistry } from "../../../src/core/registry";

const rawProfile = (id, markers, rules = []) => ({ id, description: `${id} profile`, markers, rules });
const rawRule = (id, risk = "safe") => ({
    id,
    paths: ["out/"],
    risk,
    requires: [],
    requiresAll: [],
    description: `${id} rule`,
});
const none = { rules: [], profileDefs: {} };

describe("built-in profiles", () => {
    it("loads the bundled profiles and indexes every rule by ID", () => {
        const { profiles, rules } = buildRegistry();
        expect(profiles.has("python")).toBe(true);
        expect(rules.size).toBeGreaterThan(0);
        for (const rule of rules.values()) expect(profiles.get(rule.profile).rules).toContain(rule);
    });

    it("marks built-in rules and gives them a numeric-ready risk name", () => {
        const { rules } = buildRegistry([rawProfile("p", ["p.txt"], [rawRule("p.a", "High_Impact")])], none);
        expect(rules.get("p.a")).toMatchObject({
            profile: "p",
            risk: "high-impact",
            builtin: true,
            allowUntracked: false,
        });
    });

    it("treats a profile without markers as always active", () => {
        const { profiles } = buildRegistry([rawProfile("always", []), rawProfile("marked", ["m.txt"])], none);
        expect(profiles.get("always").always).toBe(true);
        expect(profiles.get("marked").always).toBe(false);
    });

    it("rejects an invalid risk level", () => {
        expect(() => buildRegistry([rawProfile("p", [], [rawRule("p.a", "scary")])], none)).toThrow(
            /Invalid risk level/,
        );
    });
});

describe("custom profiles", () => {
    it("adds markers and a description to an existing profile", () => {
        const { profiles } = buildRegistry([rawProfile("p", ["a.txt"], [rawRule("p.a")])], {
            rules: [],
            profileDefs: { p: { markers: ["b.txt"], description: "Changed" } },
        });
        expect(profiles.get("p")).toMatchObject({ markers: ["a.txt", "b.txt"], description: "Changed" });
        expect(profiles.get("p").rules).toHaveLength(1);
    });

    it("keeps the existing description when none is given", () => {
        const { profiles } = buildRegistry([rawProfile("p", ["a.txt"])], {
            rules: [],
            profileDefs: { p: { markers: ["b.txt"], description: "" } },
        });
        expect(profiles.get("p").description).toBe("p profile");
    });

    it("creates a new profile", () => {
        const { profiles } = buildRegistry([], {
            rules: [],
            profileDefs: { mine: { markers: ["m.txt"], description: "Mine" } },
        });
        expect(profiles.get("mine")).toMatchObject({
            id: "mine",
            description: "Mine",
            markers: ["m.txt"],
            always: false,
            rules: [],
        });
    });
});

describe("custom rules", () => {
    it("attaches a rule to its existing profile", () => {
        const rule = { id: "p.extra", profile: "p", paths: ["x/"] };
        const { profiles, rules } = buildRegistry([rawProfile("p", ["a.txt"], [rawRule("p.a")])], {
            rules: [rule],
            profileDefs: {},
        });
        expect(profiles.get("p").rules.map((r) => r.id)).toEqual(["p.a", "p.extra"]);
        expect(rules.get("p.extra")).toBe(rule);
    });

    it("creates an always-active user profile for an unknown profile name", () => {
        const rule = { id: "team.out", profile: "custom", paths: ["out/"] };
        const { profiles } = buildRegistry([], { rules: [rule], profileDefs: {} });
        expect(profiles.get("custom")).toMatchObject({ description: "User-defined rules", always: true });
    });

    it("rejects a rule ID that is already taken", () => {
        const rule = { id: "p.a", profile: "p", paths: ["x/"] };
        expect(() =>
            buildRegistry([rawProfile("p", [], [rawRule("p.a")])], { rules: [rule], profileDefs: {} }),
        ).toThrow(/Duplicate rule ID 'p.a'/);
    });
});
