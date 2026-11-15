import { formatSize } from "./models";

// ANSI-coloured tables for the Sweepito terminal. With colour off (the CLI's --no-color) the
// same text is produced without escape codes.

/** Style functions; each returns its argument unchanged when `enabled` is false. */
export function styles(enabled = true) {
    const wrap = (code) => (text) => (enabled ? `\x1b[${code}m${text}\x1b[0m` : String(text));
    const s = {
        bold: wrap(1),
        dim: wrap(2),
        red: wrap(31),
        green: wrap(32),
        yellow: wrap(33),
        blue: wrap(34),
        cyan: wrap(36),
    };
    s.risk = (risk) =>
        ({ safe: s.green, configurable: s.yellow, "high-impact": s.red, custom: s.blue })[risk] ?? String;
    return s;
}

const rawLength = (text) => String(text).length;

/**
 * A table with a coloured header. Cells are strings, or [string, style] to colour one cell;
 * widths are measured before styling so colours never break the alignment.
 */
export function textTable(title, header, rows, c) {
    const cells = rows.map((row) => row.map((cell) => (Array.isArray(cell) ? cell : [String(cell), String])));
    const widths = header.map((h, i) => Math.max(rawLength(h), ...cells.map((row) => rawLength(row[i][0]))));
    const pad = (text, i) => text + " ".repeat(widths[i] - rawLength(text));
    const lines = [];
    if (title) lines.push(c.bold(title));
    lines.push(header.map((h, i) => c.bold(c.cyan(pad(h, i)))).join("  "));
    lines.push(c.dim(widths.map((w) => "-".repeat(w)).join("  ")));
    for (const row of cells) lines.push(row.map(([text, style], i) => style(pad(text, i))).join("  "));
    return lines.join("\n");
}

/** A scan: one row per candidate and a summary line. */
export function planTerminal(plan, name, c) {
    if (plan.candidates.length === 0) return `${c.bold(`Scan of ${name}`)}\n${c.green("Nothing to clean.")}`;
    const rows = plan.candidates.map((x) => [
        [x.risk, c.risk(x.risk)],
        x.rule,
        `${x.path}${x.isDir ? "/" : ""}`,
        formatSize(x.size),
    ]);
    const skipped = plan.skipped.length ? c.dim(`  (${plan.skipped.length} skipped)`) : "";
    return [
        textTable(
            `Scan of ${name} (${plan.profiles.join(", ") || "no profiles"})`,
            ["Risk", "Rule", "Path", "Size"],
            rows,
            c,
        ),
        `${c.bold(`${plan.candidates.length} item(s), ${formatSize(plan.totalBytes)} reclaimable.`)}${skipped}`,
    ].join("\n");
}

/** The outcome of a clean. */
export function cleanTerminal(result, c) {
    const lines = [
        `${c.bold(c.green(`Freed ${formatSize(result.freedBytes)}`))}  ${result.removed.length} removed, ` +
            `${result.skipped.length} skipped, ${result.failed.length ? c.red(`${result.failed.length} failed`) : "0 failed"}`,
    ];
    for (const s of result.skipped) lines.push(c.dim(`  skipped ${s.path}: ${s.reason}`));
    for (const f of result.failed) lines.push(c.red(`  failed ${f.path}: ${f.error}`));
    return lines.join("\n");
}

/** Reclaimable space by profile, rule and risk. */
export function reportTerminal(report, c) {
    const bySize = ([, a], [, b]) => b.bytes - a.bytes;
    const row = ([key, slot]) => [key, String(slot.count), formatSize(slot.bytes)];
    return [
        c.bold(`Report for ${report.root}: ${formatSize(report.totalBytes)} reclaimable`),
        textTable("By profile", ["Profile", "Items", "Size"], Object.entries(report.profile).sort(bySize).map(row), c),
        textTable(
            "By rule",
            ["Rule", "Risk", "Items", "Size"],
            Object.entries(report.rule)
                .sort(bySize)
                .map(([key, slot]) => [
                    key,
                    [slot.risk, c.risk(slot.risk)],
                    String(slot.count),
                    formatSize(slot.bytes),
                ]),
            c,
        ),
        textTable(
            "By risk",
            ["Risk", "Items", "Size"],
            Object.entries(report.risk)
                .sort(bySize)
                .map(([key, slot]) => [[key, c.risk(key)], String(slot.count), formatSize(slot.bytes)]),
            c,
        ),
    ].join("\n\n");
}

/** Doctor results. */
export function checksTerminal(checks, c) {
    const rows = checks.map((x) => [
        x.name,
        x.ok ? ["ok", c.green] : x.required ? ["FAIL", c.red] : ["warn", c.yellow],
        x.detail,
    ]);
    const healthy = checks.filter((x) => x.required).every((x) => x.ok);
    return [
        textTable("Doctor", ["Check", "Status", "Detail"], rows, c),
        healthy ? c.green("Healthy.") : c.red("Not healthy: a required check failed."),
    ].join("\n");
}

/**
 * Rules as a table, with the same optional filters as `sweepito rules`.
 * @param {any} registry
 * @param {{ profiles?: string[], risk?: string | null }} filter
 * @param {ReturnType<typeof styles>} c
 */
export function rulesTerminal(registry, { profiles = [], risk = null } = {}, c) {
    const rows = [];
    for (const profile of registry.profiles.values()) {
        if (profiles.length && !profiles.includes(profile.id)) continue;
        for (const rule of profile.rules) {
            if (risk && rule.risk !== risk) continue;
            const on = rule.risk === "safe" || rule.risk === "custom";
            rows.push([
                profile.id,
                rule.id,
                [rule.risk, c.risk(rule.risk)],
                on ? ["on", c.green] : "opt-in",
                rule.description,
            ]);
        }
    }
    return textTable("Sweepito rules", ["Profile", "Rule", "Risk", "Default", "Description"], rows, c);
}
