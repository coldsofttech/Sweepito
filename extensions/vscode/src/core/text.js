import { formatSize } from "./models";

// Plain text for the Sweepito output channel: no colour, one fact per line.

/** A scan: one line per candidate, then a summary. */
export function planText(plan, name = plan.root) {
    const lines = [`Scan of ${name} (${plan.profiles.join(", ") || "no profiles"})`];
    for (const c of plan.candidates) {
        lines.push(`  ${c.risk.padEnd(12)} ${c.rule.padEnd(28)} ${c.path}${c.isDir ? "/" : ""}  ${formatSize(c.size)}`);
    }
    if (plan.skipped.length) lines.push(`  ${plan.skipped.length} skipped`);
    lines.push(`${plan.candidates.length} item(s), ${formatSize(plan.totalBytes)} reclaimable.`);
    return lines.join("\n");
}

/** The outcome of a clean. */
export function cleanText(result, name = "") {
    const lines = [`Clean${name ? ` of ${name}` : ""}: freed ${formatSize(result.freedBytes)}`];
    lines.push(`  ${result.removed.length} removed, ${result.skipped.length} skipped, ${result.failed.length} failed`);
    for (const s of result.skipped) lines.push(`  skipped ${s.path}: ${s.reason}`);
    for (const f of result.failed) lines.push(`  failed ${f.path}: ${f.error}`);
    return lines.join("\n");
}

/** Reclaimable space by profile, rule and risk. */
export function reportText(report) {
    const lines = [`Report for ${report.root}: ${formatSize(report.totalBytes)} reclaimable`];
    for (const kind of ["profile", "rule", "risk"]) {
        lines.push(`  By ${kind}:`);
        for (const [key, slot] of Object.entries(report[kind]).sort(([, a], [, b]) => b.bytes - a.bytes)) {
            lines.push(`    ${key.padEnd(28)} ${String(slot.count).padStart(4)}  ${formatSize(slot.bytes)}`);
        }
    }
    return lines.join("\n");
}

/** Doctor results. */
export function checksText(checks) {
    return [
        "Doctor:",
        ...checks.map((c) => `  ${c.ok ? "ok  " : c.required ? "FAIL" : "warn"}  ${c.name}: ${c.detail}`),
    ].join("\n");
}
