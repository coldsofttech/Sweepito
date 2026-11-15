import { describe, expect, it } from "vitest";
import { buildReport } from "../../../src/core/report";
import { checksText, cleanText, planText, reportText } from "../../../src/core/text";

const plan = {
    root: "/w/app",
    profiles: ["python"],
    totalBytes: 1088,
    candidates: [
        { rule: "python.pycache", profile: "python", risk: "safe", path: "a/__pycache__", isDir: true, size: 1088 },
    ],
    skipped: [{ path: "x", rule: "python.pytest", reason: "tracked by git" }],
};

describe("plain text", () => {
    it("renders scan, clean, report and doctor", () => {
        expect(planText(plan, "app")).toContain("1 item(s), 1.1 KB reclaimable.");
        expect(planText(plan, "app")).toContain("a/__pycache__/");
        const result = {
            removed: [1],
            skipped: [{ path: "p", reason: "tracked by git" }],
            failed: [{ path: "q", error: "busy" }],
            freedBytes: 10,
        };
        expect(cleanText(result)).toContain("1 removed, 1 skipped, 1 failed");
        expect(cleanText(result)).toContain("failed q: busy");
        expect(reportText(buildReport(plan))).toContain("By profile:");
        expect(checksText([{ name: "Git", ok: false, detail: "NOT FOUND", required: true }])).toContain(
            "FAIL  Git: NOT FOUND",
        );
    });
});
