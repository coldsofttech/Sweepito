/** Inline code safe for a Markdown table cell. */
export const cell = (text) => `\`${String(text).replace(/[`|\r\n]/g, " ")}\``;

/** Plain text safe for a Markdown table cell. */
export const plain = (text) =>
    String(text)
        .replace(/\|/g, "\\|")
        .replace(/\s*[\r\n]+\s*/g, " ");

/** A Markdown table, or "" when there are no rows. Cells must already be escaped. */
export function table(title, header, rows, level = 2) {
    if (rows.length === 0) return "";
    const lines = [];
    if (title) lines.push(`${"#".repeat(level)} ${title}`, "");
    lines.push(`| ${header.join(" | ")} |`, `|${header.map(() => "---").join("|")}|`);
    lines.push(...rows.map((row) => `| ${row.join(" | ")} |`), "");
    return lines.join("\n");
}
