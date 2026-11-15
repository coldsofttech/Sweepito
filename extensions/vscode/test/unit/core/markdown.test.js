import { describe, expect, it } from "vitest";
import { cell, plain, table } from "../../../src/core/markdown";

describe("cell", () => {
    it("wraps text as inline code", () => {
        expect(cell("node_modules")).toBe("`node_modules`");
        expect(cell(42)).toBe("`42`");
    });

    it("replaces characters that would break the table or the code span", () => {
        expect(cell("a|b`c")).toBe("`a b c`");
        expect(cell("a\r\nb")).toBe("`a  b`");
    });
});

describe("plain", () => {
    it("escapes pipes", () => {
        expect(plain("a|b")).toBe("a\\|b");
    });

    it("collapses line breaks and the space around them into one space", () => {
        expect(plain("one \r\n  two\nthree")).toBe("one two three");
    });

    it("converts non-strings", () => {
        expect(plain(null)).toBe("null");
    });
});

describe("table", () => {
    it("renders a titled table", () => {
        expect(
            table(
                "Rules",
                ["ID", "Risk"],
                [
                    ["a", "safe"],
                    ["b", "custom"],
                ],
            ),
        ).toBe(["## Rules", "", "| ID | Risk |", "|---|---|", "| a | safe |", "| b | custom |", ""].join("\n"));
    });

    it("uses the given heading level", () => {
        expect(table("Deep", ["A"], [["x"]], 4).startsWith("#### Deep\n")).toBe(true);
    });

    it("omits the heading without a title", () => {
        expect(table("", ["A"], [["x"]]).startsWith("| A |")).toBe(true);
    });

    it("is empty when there are no rows", () => {
        expect(table("Rules", ["ID"], [])).toBe("");
    });
});
