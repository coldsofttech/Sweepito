import { passed } from "./doctor";

// Shapes match what the sweepito command line tool prints with --json.

export const candidateJson = (c) => ({
    rule: c.rule,
    profile: c.profile,
    risk: c.risk,
    path: c.path,
    is_dir: c.isDir,
    size: c.size,
});

/** `sweepito scan --json`. */
export const scanJson = (plan) => ({
    root: plan.root,
    profiles: plan.profiles,
    candidates: plan.candidates.map(candidateJson),
    skipped: plan.skipped.map((s) => ({ path: s.path, rule: s.rule, reason: s.reason })),
    total_bytes: plan.totalBytes,
    dry_run: true,
});

/** `sweepito clean --json`: the plan that was cleaned plus what happened to it. */
export const cleanJson = (plan, result) => ({
    root: plan.root,
    profiles: plan.profiles,
    candidates: plan.candidates.map(candidateJson),
    skipped: result.skipped.map((s) => ({ path: s.path, rule: s.rule, reason: s.reason })),
    total_bytes: plan.candidates.reduce((sum, c) => sum + c.size, 0),
    dry_run: false,
    removed: result.removed.map(candidateJson),
    failed: result.failed.map((f) => ({ path: f.path, error: f.error })),
    freed_bytes: result.freedBytes,
});

/** `sweepito report --json`. */
export const reportJson = (report) => ({
    root: report.root,
    total_bytes: report.totalBytes,
    profile: report.profile,
    rule: report.rule,
    risk: report.risk,
});

/** `sweepito doctor --json`. */
export const doctorJson = (checks) => ({
    healthy: passed(checks),
    checks: checks.map((c) => ({ name: c.name, ok: c.ok, detail: c.detail, required: c.required })),
});

/** `sweepito rules --json`, with the same optional profile and risk filters. */
export function rulesJson(registry, { profiles = [], risk = null } = {}) {
    const rules = [];
    for (const profile of registry.profiles.values()) {
        if (profiles.length && !profiles.includes(profile.id)) continue;
        for (const rule of profile.rules) {
            if (risk && rule.risk !== risk) continue;
            rules.push({
                id: rule.id,
                profile: rule.profile,
                risk: rule.risk,
                default: rule.risk === "safe" || rule.risk === "custom",
                description: rule.description,
            });
        }
    }
    return { rules };
}

/** `sweepito profiles --json`. */
export function profilesJson(registry) {
    return {
        profiles: [...registry.profiles.values()].map((p) => {
            const counts = { safe: 0, configurable: 0, high_impact: 0, custom: 0 };
            for (const rule of p.rules) counts[rule.risk.replace(/-/g, "_")] += 1;
            return {
                id: p.id,
                description: p.description,
                markers: p.markers,
                always_active: p.always,
                rules: p.rules.length,
                ...counts,
            };
        }),
    };
}

/** `sweepito config --json`. */
export const configJson = ({ settings, configPath, registry }) => ({
    config_file: configPath,
    settings: {
        profiles: settings.profiles,
        risk: settings.risk,
        enable: settings.enable,
        disable: settings.disable,
        exclude: settings.exclude,
        no_git_check: settings.noGitCheck,
        quiet: false,
    },
    custom_rules: [...registry.rules.values()].filter((r) => !r.builtin).map((r) => r.id),
});
