// Prepares the files the extension takes from the rest of the repository, so each has one
// source of truth: the built-in profiles (the Python package's TOML files) as one JSON file,
// so the extension needs neither Python nor a TOML parser; and the starter config.
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "smol-toml";

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "..", "..", "..", "python", "src", "sweepito", "profiles");
const target = join(here, "..", "src", "core", "profiles.json");

const profiles = readdirSync(source)
    .filter((name) => name.endsWith(".toml"))
    .sort()
    .map((name) => {
        const data = parse(readFileSync(join(source, name), "utf8"));
        return {
            id: data.id,
            description: data.description ?? "",
            markers: data.markers ?? [],
            rules: (data.rule ?? []).map((rule) => ({
                id: rule.id,
                paths: rule.paths,
                risk: rule.risk,
                requires: rule.requires ?? [],
                requiresAll: rule.requires_all ?? [],
                description: rule.description ?? "",
            })),
        };
    });

writeFileSync(target, JSON.stringify(profiles));

// The starter config written by "Create Config File", shared with `sweepito init`.
const template = join(here, "..", "..", "..", "python", "src", "sweepito", "cli", "templates", "sweepito.toml.tmpl");
writeFileSync(join(here, "..", "src", "core", "config-template.json"), JSON.stringify(readFileSync(template, "utf8")));

console.log(`Bundled ${profiles.length} profiles.`);
