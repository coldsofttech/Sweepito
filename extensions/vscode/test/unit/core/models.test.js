import { describe, expect, it } from "vitest";
import { RISK, formatSize, parseRisk } from "../../../src/core/models";

describe("RISK", () => {
    it("orders custom below safe below configurable below high-impact", () => {
        expect(RISK.custom).toBeLessThan(RISK.safe);
        expect(RISK.safe).toBeLessThan(RISK.configurable);
        expect(RISK.configurable).toBeLessThan(RISK["high-impact"]);
    });
});

describe("parseRisk", () => {
    it("accepts every level", () => {
        for (const level of Object.keys(RISK)) expect(parseRisk(level)).toBe(level);
    });

    it("ignores case and surrounding space, and accepts underscores", () => {
        expect(parseRisk("  Safe ")).toBe("safe");
        expect(parseRisk("HIGH_IMPACT")).toBe("high-impact");
    });

    it("rejects anything else", () => {
        expect(() => parseRisk("risky")).toThrow(/Invalid risk level 'risky'/);
        expect(() => parseRisk("")).toThrow(/Invalid risk level/);
    });
});

describe("formatSize", () => {
    it("shows bytes as whole numbers", () => {
        expect(formatSize(0)).toBe("0 B");
        expect(formatSize(512)).toBe("512 B");
        expect(formatSize(1023)).toBe("1023 B");
    });

    it("scales by 1024 with one decimal", () => {
        expect(formatSize(1024)).toBe("1.0 KB");
        expect(formatSize(1536)).toBe("1.5 KB");
        expect(formatSize(1024 ** 2)).toBe("1.0 MB");
        expect(formatSize(5 * 1024 ** 3)).toBe("5.0 GB");
    });

    it("stops at terabytes", () => {
        expect(formatSize(2048 * 1024 ** 4)).toBe("2048.0 TB");
    });
});
