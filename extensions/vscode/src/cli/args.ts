import type { Risk } from "./types";

/** The extension settings that map to command line flags. */
export interface Selection {
  risk?: Risk;
  enable: string[];
  disable: string[];
  exclude: string[];
  configFile?: string;
  profiles?: string[];
}

const RISK_ORDER: Risk[] = ["custom", "safe", "configurable", "high-impact"];

export function riskRank(risk: Risk): number {
  return RISK_ORDER.indexOf(risk);
}

/** A risk is "higher" when it needs an explicit opt-in: above `safe`. */
export function isHigherRisk(risk: Risk): boolean {
  return riskRank(risk) > riskRank("safe");
}

/**
 * Global options (`--config`) go before nothing special: argparse accepts them on the
 * subcommand, so every flag is appended after the subcommand name and PATH.
 */
export function selectionArgs(sel: Selection): string[] {
  const args: string[] = [];
  if (sel.configFile) {
    args.push("--config", sel.configFile);
  }
  if (sel.risk) {
    args.push("--risk", sel.risk);
  }
  for (const profile of sel.profiles ?? []) {
    args.push("--profile", profile);
  }
  for (const rule of dedupe(sel.enable)) {
    args.push("--enable", rule);
  }
  for (const rule of dedupe(sel.disable)) {
    args.push("--disable", rule);
  }
  for (const pattern of dedupe(sel.exclude)) {
    args.push("--exclude", pattern);
  }
  return args;
}

export function scanArgs(root: string, sel: Selection): string[] {
  return ["scan", root, ...selectionArgs(sel)];
}

export function cleanDryRunArgs(root: string, sel: Selection): string[] {
  return ["clean", root, ...selectionArgs(sel), "--dry-run"];
}

/** `--yes` is only ever added after the user confirmed the dry run built from the same `sel`. */
export function cleanArgs(root: string, sel: Selection): string[] {
  return ["clean", root, ...selectionArgs(sel), "--yes"];
}

/**
 * Narrow a selection to exactly one rule. The CLI has no "only this rule" flag, so every
 * other rule is disabled (`--disable` always wins) and the target is enabled.
 */
export function onlyRule(sel: Selection, rule: string, allRules: string[]): Selection {
  return {
    ...sel,
    enable: [...sel.enable.filter((r) => r !== rule), rule],
    disable: dedupe([...sel.disable, ...allRules.filter((r) => r !== rule)]).filter(
      (r) => r !== rule,
    ),
  };
}

export function onlyProfile(sel: Selection, profile: string): Selection {
  return { ...sel, profiles: [profile] };
}

function dedupe(items: string[]): string[] {
  return [...new Set(items.map((s) => s.trim()).filter(Boolean))];
}

export function formatSize(size: number): string {
  let value = size;
  for (const unit of ["B", "KB", "MB", "GB", "TB"]) {
    if (value < 1024 || unit === "TB") {
      return unit === "B" ? `${Math.trunc(value)} B` : `${value.toFixed(1)} ${unit}`;
    }
    value /= 1024;
  }
  return `${size} B`;
}
