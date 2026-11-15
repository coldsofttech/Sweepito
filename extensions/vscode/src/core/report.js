import { cell, table } from "./markdown";
import { RISK, formatSize } from "./models";

/**
 * Totals the candidates of a plan by profile, rule and risk level:
 * { root, totalBytes, profile, rule, risk }, where each group maps a key to { count, bytes }
 * (rules also carry their `risk`).
 */
export function buildReport(plan) {
    const groups = { profile: {}, rule: {}, risk: {} };
    for (const cand of plan.candidates) {
        for (const [kind, key] of [
            ["profile", cand.profile],
            ["rule", cand.rule],
            ["risk", cand.risk],
        ]) {
            const slot = (groups[kind][key] ??= { count: 0, bytes: 0 });
            if (kind === "rule") slot.risk = cand.risk;
            slot.count += 1;
            slot.bytes += cand.size;
        }
    }
    return { root: plan.root, totalBytes: plan.totalBytes, ...groups };
}

/** Renders a report as Markdown. */
export function formatReport(report) {
    const bySize = ([, a], [, b]) => b.bytes - a.bytes;
    const byRisk = ([a], [b]) => RISK[a] - RISK[b];
    const count = (slot) => `${slot.count} | ${formatSize(slot.bytes)}`;
    const parts = [
        "# Sweepito report",
        "",
        `Everything that could be cleaned at any risk level in ${cell(report.root)}. Nothing is deleted.`,
        "",
        `**Total reclaimable: ${formatSize(report.totalBytes)}**`,
        "",
    ];
    if (report.totalBytes === 0 && Object.keys(report.rule).length === 0) {
        parts.push("Nothing to clean.", "");
        return parts.join("\n");
    }
    parts.push(
        table(
            "By profile",
            ["Profile", "Items", "Size"],
            Object.entries(report.profile)
                .sort(bySize)
                .map(([k, v]) => [cell(k), count(v)]),
        ),
        table(
            "By rule",
            ["Rule", "Risk", "Items", "Size"],
            Object.entries(report.rule)
                .sort(bySize)
                .map(([k, v]) => [cell(k), v.risk, count(v)]),
        ),
        table(
            "By risk",
            ["Risk", "Items", "Size"],
            Object.entries(report.risk)
                .sort(byRisk)
                .map(([k, v]) => [k, count(v)]),
        ),
    );
    return parts.join("\n");
}
