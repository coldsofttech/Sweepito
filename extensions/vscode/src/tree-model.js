import { formatSize } from "./core/models";

export const sumSize = (items) => items.reduce((total, c) => total + c.size, 0);

/** Groups items by `key`, sorted by key. */
export function groupBy(items, key) {
    const map = new Map();
    for (const item of items) {
        const k = key(item);
        if (!map.has(k)) map.set(k, []);
        map.get(k).push(item);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
}

function profileNodes(candidates) {
    return groupBy(candidates, (c) => c.profile).map(([profile, items]) => ({
        kind: "profile",
        label: profile,
        items,
        expandable: true,
        description: formatSize(sumSize(items)),
    }));
}

/**
 * The children of a tree node as plain data. `entries` has one item per workspace folder:
 * { name, root, plan, error }. With several folders the top level is the folders; with one it
 * is the profiles. Below that: profiles, then rules, then the candidate paths.
 * `descriptions` maps a rule ID to its description.
 */
export function childrenOf(entries, node, descriptions) {
    if (!node) {
        if (entries.length > 1) {
            return entries.map((e) =>
                e.plan
                    ? {
                          kind: "workspace",
                          label: e.name,
                          items: e.plan.candidates,
                          root: e.root,
                          expandable: e.plan.candidates.length > 0,
                          description: formatSize(e.plan.totalBytes),
                          tooltip: e.root,
                      }
                    : {
                          kind: "error",
                          label: e.name,
                          items: [],
                          expandable: false,
                          description: "failed",
                          tooltip: e.error ?? "",
                      },
            );
        }
        return entries.length === 1 && entries[0].plan ? profileNodes(entries[0].plan.candidates) : [];
    }
    if (node.kind === "workspace") return profileNodes(node.items);
    if (node.kind === "profile") {
        return groupBy(node.items, (c) => c.rule).map(([rule, items]) => ({
            kind: "rule",
            label: rule,
            items,
            expandable: true,
            description: formatSize(sumSize(items)),
            tooltip: descriptions.get(rule) ?? "",
        }));
    }
    if (node.kind === "rule") {
        return node.items.map((c) => ({
            kind: "folder",
            label: c.path,
            items: [c],
            expandable: false,
            isDir: c.isDir,
            description: formatSize(c.size),
            tooltip: `${c.rule} (${c.risk})`,
        }));
    }
    return [];
}
