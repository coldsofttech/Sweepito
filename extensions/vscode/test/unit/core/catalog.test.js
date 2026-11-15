import { describe, expect, it } from "vitest";
import { profileMarkdown, profilesMarkdown, ruleMarkdown, rulesMarkdown } from "../../../src/core/catalog";
import { buildRegistry } from "../../../src/core/registry";

const custom = {
    rules: [
        {
            id: "team.out",
            profile: "myteam",
            paths: ["out/"],
            risk: "custom",
            requires: [],
            requiresAll: [],
            description: "Build | output",
            allowUntracked: true,
            builtin: false,
        },
    ],
    profileDefs: { myteam: { markers: ["Teamfile"], description: "Our team" } },
};
const registry = buildRegistry(undefined, custom);

describe("rulesMarkdown", () => {
    it("lists every rule with its default state", () => {
        const text = rulesMarkdown(registry);
        expect(text).toContain("| `python` | `python.pycache` | safe | on |");
        expect(text).toContain("| `myteam` | `team.out` | custom | on | Build \\| output |");
        expect(text).toContain("opt-in");
    });

    it("filters by profile and risk", () => {
        const text = rulesMarkdown(registry, { profiles: ["python"], risk: "safe" });
        expect(text).toContain("`python.pycache`");
        expect(text).not.toContain("`team.out`");
        expect(text).not.toContain("| configurable |");
        expect(rulesMarkdown(registry, { profiles: ["myteam"], risk: "safe" })).toContain("No rules match.");
    });
});

describe("profilesMarkdown", () => {
    it("shows markers, counts and a Custom column only when needed", () => {
        expect(profilesMarkdown(registry)).toContain("| Custom |");
        expect(profilesMarkdown(buildRegistry())).not.toContain("| Custom |");
        expect(profilesMarkdown(registry)).toContain("| `myteam` | Our team | `Teamfile` |");
        expect(profilesMarkdown(registry)).toContain("always active");
    });
});

describe("details", () => {
    it("explains a rule using the profile markers when it has none", () => {
        const text = ruleMarkdown(registry, "python.pytest");
        expect(text).toContain("# Rule `python.pytest`");
        expect(text).toContain("`pyproject.toml`");
        expect(text).toContain("**Matches untracked files:** no");
        expect(ruleMarkdown(registry, "team.out")).toContain("**Matches untracked files:** yes");
    });

    it("explains a profile with its rules", () => {
        const text = profileMarkdown(registry, "myteam");
        expect(text).toContain("# Profile `myteam`");
        expect(text).toContain("`team.out`");
    });

    it("rejects unknown IDs", () => {
        expect(() => ruleMarkdown(registry, "nope")).toThrow(/Unknown rule ID 'nope'/);
        expect(() => profileMarkdown(registry, "nope")).toThrow(/Unknown profile 'nope'/);
    });
});
