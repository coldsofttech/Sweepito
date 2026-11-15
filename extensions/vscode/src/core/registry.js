import profilesData from "./profiles.json";
import { parseRisk } from "./models";

function build(raw) {
    return {
        id: raw.id,
        description: raw.description,
        markers: [...raw.markers],
        always: raw.markers.length === 0,
        rules: raw.rules,
    };
}

/**
 * Loads the bundled built-in profiles, then merges user-defined profiles and rules.
 * `custom` is { rules, profileDefs } as returned by mergeConfig.
 */
export function buildRegistry(raw = profilesData, custom = { rules: [], profileDefs: {} }) {
    const profiles = new Map();
    for (const profile of raw) {
        profiles.set(
            profile.id,
            build({
                ...profile,
                rules: profile.rules.map((rule) => ({
                    id: rule.id,
                    profile: profile.id,
                    paths: rule.paths,
                    risk: parseRisk(rule.risk),
                    requires: rule.requires,
                    requiresAll: rule.requiresAll,
                    description: rule.description,
                    allowUntracked: false,
                    builtin: true,
                })),
            }),
        );
    }

    for (const [name, def] of Object.entries(custom.profileDefs)) {
        const existing = profiles.get(name);
        profiles.set(
            name,
            existing
                ? build({
                      ...existing,
                      markers: [...existing.markers, ...def.markers],
                      description: def.description || existing.description,
                  })
                : build({ id: name, description: def.description, markers: def.markers, rules: [] }),
        );
    }
    for (const rule of custom.rules) {
        const profile =
            profiles.get(rule.profile) ??
            build({ id: rule.profile, description: "User-defined rules", markers: [], rules: [] });
        profiles.set(rule.profile, { ...profile, rules: [...profile.rules, rule] });
    }

    const rules = new Map();
    for (const profile of profiles.values()) {
        for (const rule of profile.rules) {
            if (rules.has(rule.id)) throw new Error(`Duplicate rule ID '${rule.id}'.`);
            rules.set(rule.id, rule);
        }
    }
    return { profiles, rules };
}
