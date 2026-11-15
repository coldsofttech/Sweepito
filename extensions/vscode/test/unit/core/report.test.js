import { describe, expect, it } from "vitest";
import { buildReport, formatReport } from "../../../src/core/report";

const plan = {
    root: "/work/app",
    totalBytes: 3136,
    candidates: [
        { rule: "python.pycache", profile: "python", risk: "safe", path: "a/__pycache__", isDir: true, size: 1024 },
        { rule: "python.pycache", profile: "python", risk: "safe", path: "b/__pycache__", isDir: true, size: 64 },
        { rule: "node.modules", profile: "node", risk: "high-impact", path: "node_modules", isDir: true, size: 2048 },
    ],
};

describe("buildReport", () => {
    it("totals by profile, rule and risk", () => {
        const report = buildReport(plan);
        expect(report.profile.python).toEqual({ count: 2, bytes: 1088 });
        expect(report.rule["python.pycache"]).toEqual({ count: 2, bytes: 1088, risk: "safe" });
        expect(report.risk["high-impact"]).toEqual({ count: 1, bytes: 2048 });
        expect(report.totalBytes).toBe(3136);
    });
});

describe("formatReport", () => {
    it("renders three tables, largest first, risks in order", () => {
        const text = formatReport(buildReport(plan));
        expect(text).toContain("**Total reclaimable: 3.1 KB**");
        expect(text.indexOf("`node`")).toBeLessThan(text.indexOf("`python`"));
        const risks = text.slice(text.indexOf("## By risk"));
        expect(risks.indexOf("| safe |")).toBeLessThan(risks.indexOf("| high-impact |"));
        expect(text).toContain("## By profile");
        expect(text).toContain("## By rule");
        expect(text).toContain("## By risk");
    });

    it("escapes table separators in names", () => {
        const text = formatReport(
            buildReport({ ...plan, candidates: [{ ...plan.candidates[0], rule: "a|b", profile: "p`q" }] }),
        );
        expect(text).toContain("`a b`");
        expect(text).toContain("`p q`");
    });

    it("says so when there is nothing to clean", () => {
        expect(formatReport(buildReport({ root: "/x", totalBytes: 0, candidates: [] }))).toContain("Nothing to clean.");
    });
});
