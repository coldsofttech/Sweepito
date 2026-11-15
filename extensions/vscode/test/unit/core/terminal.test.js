import { describe, expect, it } from "vitest";
import { cleanJson } from "../../../src/core/json";
import { buildRegistry } from "../../../src/core/registry";
import { buildReport } from "../../../src/core/report";
import {
    checksTerminal,
    cleanTerminal,
    planTerminal,
    reportTerminal,
    rulesTerminal,
    styles,
    textTable,
} from "../../../src/core/terminal";

const ESC = String.fromCharCode(27);
const plan = {
    root: "/w/app",
    profiles: ["python"],
    totalBytes: 1088,
    candidates: [
        { rule: "python.pycache", profile: "python", risk: "safe", path: "a/__pycache__", isDir: true, size: 1024 },
        { rule: "node.modules", profile: "node", risk: "high-impact", path: "node_modules", isDir: true, size: 64 },
    ],
    skipped: [{ path: "x", rule: "python.pytest", reason: "tracked by git" }],
};
const strip = (text) => text.replace(new RegExp(`${ESC}\\[[0-9;]*m`, "g"), "");

describe("colour switch", () => {
    it("emits escape codes only when enabled, with identical text otherwise", () => {
        const on = planTerminal(plan, "app", styles(true));
        const off = planTerminal(plan, "app", styles(false));
        expect(on).toContain(ESC);
        expect(off).not.toContain(ESC);
        expect(strip(on)).toBe(off);
    });

    it("colours risks by severity", () => {
        const c = styles(true);
        expect(c.risk("safe")("x")).toContain(`${ESC}[32m`);
        expect(c.risk("high-impact")("x")).toContain(`${ESC}[31m`);
        expect(c.risk("nope")("x")).toBe("x");
    });
});

describe("tables", () => {
    it("align columns by visible width even when cells are coloured", () => {
        const c = styles(true);
        const text = strip(
            textTable(
                "T",
                ["A", "Bee"],
                [
                    [["x", c.red], "1"],
                    ["longer", "2"],
                ],
                c,
            ),
        );
        const lines = text.split("\n");
        expect(lines[1].indexOf("Bee")).toBe(lines[3].indexOf("1"));
        expect(lines[3].indexOf("1")).toBe(lines[4].indexOf("2"));
    });
});

describe("renderers", () => {
    const c = styles(false);

    it("scan lists candidates, a summary and skipped count", () => {
        const text = planTerminal(plan, "app", c);
        expect(text).toContain("a/__pycache__/");
        expect(text).toContain("2 item(s), 1.1 KB reclaimable.");
        expect(text).toContain("(1 skipped)");
        expect(planTerminal({ ...plan, candidates: [], skipped: [] }, "app", c)).toContain("Nothing to clean.");
    });

    it("clean shows counts and failures", () => {
        const text = cleanTerminal(
            { removed: [1], skipped: [], failed: [{ path: "q", error: "busy" }], freedBytes: 2048 },
            c,
        );
        expect(text).toContain("Freed 2.0 KB");
        expect(text).toContain("1 failed");
        expect(text).toContain("failed q: busy");
    });

    it("report, doctor and rules render tables", () => {
        expect(reportTerminal(buildReport(plan), c)).toContain("By rule");
        const checks = [{ name: "Git", ok: false, detail: "NOT FOUND", required: true }];
        expect(checksTerminal(checks, c)).toContain("FAIL");
        expect(checksTerminal(checks, c)).toContain("Not healthy");
        expect(rulesTerminal(buildRegistry(), { profiles: ["python"], risk: "safe" }, c)).toContain("python.pycache");
    });
});

describe("cleanJson", () => {
    it("matches clean --json: plan fields, then what happened", () => {
        const result = {
            removed: [plan.candidates[0]],
            failed: [{ path: "b", error: "busy" }],
            skipped: [{ path: "x", rule: "python.pytest", reason: "tracked by git" }],
            freedBytes: 1024,
        };
        const json = cleanJson(plan, result);
        expect(Object.keys(json)).toEqual([
            "root",
            "profiles",
            "candidates",
            "skipped",
            "total_bytes",
            "dry_run",
            "removed",
            "failed",
            "freed_bytes",
        ]);
        expect(json).toMatchObject({ dry_run: false, total_bytes: 1088, freed_bytes: 1024 });
        expect(json.removed[0]).toEqual({
            rule: "python.pycache",
            profile: "python",
            risk: "safe",
            path: "a/__pycache__",
            is_dir: true,
            size: 1024,
        });
        expect(json.failed).toEqual([{ path: "b", error: "busy" }]);
    });
});
