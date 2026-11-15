import { cell, plain, table } from "./markdown";

const RISKS = ["custom", "safe", "configurable", "high-impact"];
const isDefault = (rule) => rule.risk === "safe" || rule.risk === "custom";

function riskCounts(profile) {
    const counts = { safe: 0, configurable: 0, "high-impact": 0, custom: 0 };
    for (const rule of profile.rules) counts[rule.risk] += 1;
    return counts;
}

/** The markers of which one must exist for a rule: its own, else the profile's. */
function anyMarkers(rule, profile) {
    return rule.requires.length ? rule.requires : rule.requiresAll.length ? [] : profile.markers;
}

const list = (items) => (items.length ? items.map(cell).join(", ") : "none");

/**
 * All rules as a Markdown table, optionally limited to some profiles and one risk level.
 * @param {any} registry
 * @param {{ profiles?: string[], risk?: string | null }} [filter]
 */
export function rulesMarkdown(registry, { profiles = [], risk = null } = {}) {
    const rows = [];
    for (const profile of registry.profiles.values()) {
        if (profiles.length && !profiles.includes(profile.id)) continue;
        for (const rule of profile.rules) {
            if (risk && rule.risk !== risk) continue;
            rows.push([
                cell(profile.id),
                cell(rule.id),
                rule.risk,
                isDefault(rule) ? "on" : "opt-in",
                plain(rule.description),
            ]);
        }
    }
    const filters = [profiles.length ? `profiles: ${profiles.join(", ")}` : "", risk ? `risk: ${risk}` : ""].filter(
        Boolean,
    );
    return [
        "# Sweepito rules",
        "",
        filters.length ? `Filtered by ${filters.join("; ")}.\n` : "",
        rows.length
            ? `${rows.length} rule(s). Rules marked \`opt-in\` need a higher risk level or \`sweepito.enableRules\`.\n`
            : "No rules match.\n",
        table("", ["Profile", "Rule", "Risk", "Default", "Description"], rows),
    ].join("\n");
}

/** All profiles as a Markdown table. */
export function profilesMarkdown(registry) {
    const profiles = [...registry.profiles.values()];
    const showCustom = profiles.some((p) => riskCounts(p).custom > 0);
    const header = ["Profile", "Description", "Detected by", "Rules", "Safe", "Configurable", "High-impact"];
    if (showCustom) header.push("Custom");
    const rows = profiles.map((profile) => {
        const counts = riskCounts(profile);
        const row = [
            cell(profile.id),
            plain(profile.description),
            profile.markers.length ? profile.markers.map(cell).join(", ") : "always active",
            profile.rules.length,
            counts.safe,
            counts.configurable,
            counts["high-impact"],
        ];
        if (showCustom) row.push(counts.custom);
        return row;
    });
    return ["# Sweepito profiles", "", `${profiles.length} profile(s).\n`, table("", header, rows)].join("\n");
}

/** One rule in detail. Throws for an unknown ID. */
export function ruleMarkdown(registry, id) {
    const rule = registry.rules.get(id);
    if (!rule) throw new Error(`Unknown rule ID '${id}'.`);
    const profile = registry.profiles.get(rule.profile);
    return [
        `# Rule ${cell(rule.id)}`,
        "",
        rule.description ? `${plain(rule.description)}\n` : "",
        `- **Profile:** ${cell(rule.profile)}`,
        `- **Risk:** ${rule.risk} (${isDefault(rule) ? "on by default" : "opt-in"})`,
        `- **Paths:** ${list(rule.paths)}`,
        `- **Needs one of:** ${list(anyMarkers(rule, profile))}`,
        `- **Needs all of:** ${list(rule.requiresAll)}`,
        `- **Matches untracked files:** ${rule.allowUntracked ? "yes" : "no"}`,
        "",
    ].join("\n");
}

/** One profile in detail, with its rules. Throws for an unknown ID. */
export function profileMarkdown(registry, id) {
    const profile = registry.profiles.get(id);
    if (!profile) throw new Error(`Unknown profile '${id}'.`);
    const rows = profile.rules.map((r) => [cell(r.id), r.risk, isDefault(r) ? "on" : "opt-in", plain(r.description)]);
    return [
        `# Profile ${cell(profile.id)}`,
        "",
        profile.description ? `${plain(profile.description)}\n` : "",
        `- **Detected by:** ${profile.markers.length ? list(profile.markers) : "always active"}`,
        `- **Rules:** ${profile.rules.length}`,
        "",
        table("Rules", ["Rule", "Risk", "Default", "Description"], rows),
    ].join("\n");
}

export { RISKS };
