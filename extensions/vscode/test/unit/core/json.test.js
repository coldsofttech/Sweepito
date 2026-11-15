import { describe, expect, it } from "vitest";
import { configJson, doctorJson, profilesJson, reportJson, rulesJson, scanJson } from "../../../src/core/json";
import { buildRegistry } from "../../../src/core/registry";
import { buildReport } from "../../../src/core/report";

const plan = {
    root: "/w/app",
    profiles: ["python"],
    totalBytes: 1088,
    candidates: [
        { rule: "python.pycache", profile: "python", risk: "safe", path: "a/__pycache__", isDir: true, size: 1088 },
    ],
    skipped: [{ path: "x", rule: "python.pytest", reason: "tracked by git" }],
};
const registry = buildRegistry();

describe("JSON shapes match the CLI", () => {
    it("scan", () => {
        expect(scanJson(plan)).toEqual({
            root: "/w/app",
            profiles: ["python"],
            candidates: [
                {
                    rule: "python.pycache",
                    profile: "python",
                    risk: "safe",
                    path: "a/__pycache__",
                    is_dir: true,
                    size: 1088,
                },
            ],
            skipped: [{ path: "x", rule: "python.pytest", reason: "tracked by git" }],
            total_bytes: 1088,
            dry_run: true,
        });
    });

    it("report, doctor, config", () => {
        expect(Object.keys(reportJson(buildReport(plan)))).toEqual(["root", "total_bytes", "profile", "rule", "risk"]);
        const checks = [
            { name: "Git", ok: true, detail: "git 2", required: true },
            { name: "x", ok: false, detail: "d", required: false },
        ];
        expect(doctorJson(checks)).toEqual({ healthy: true, checks });
        expect(doctorJson([{ ...checks[0], ok: false }]).healthy).toBe(false);
        const cfg = configJson({
            settings: { profiles: ["auto"], risk: "safe", enable: [], disable: [], exclude: [], noGitCheck: false },
            configPath: null,
            registry,
        });
        expect(cfg).toEqual({
            config_file: null,
            settings: {
                profiles: ["auto"],
                risk: "safe",
                enable: [],
                disable: [],
                exclude: [],
                no_git_check: false,
                quiet: false,
            },
            custom_rules: [],
        });
    });

    it("rules and profiles", () => {
        const rules = rulesJson(registry, { profiles: ["python"], risk: "safe" }).rules;
        expect(rules.length).toBeGreaterThan(0);
        expect(rules.every((r) => r.profile === "python" && r.risk === "safe" && r.default === true)).toBe(true);
        const python = profilesJson(registry).profiles.find((p) => p.id === "python");
        expect(python).toMatchObject({ always_active: false, custom: 0 });
        expect(python.rules).toBe(python.safe + python.configurable + python.high_impact);
    });
});
