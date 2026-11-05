import * as vscode from "vscode";
import { formatSize, isHigherRisk } from "../cli/args";
import type { Candidate, ScanResult } from "../cli/types";

const MAX_LISTED = 25;

export function describeCandidates(items: Candidate[]): string {
  const lines = items
    .slice()
    .sort((a, b) => b.size - a.size)
    .slice(0, MAX_LISTED)
    .map((c) => `${c.path}${c.is_dir ? "/" : ""}  (${c.rule}, ${c.risk}, ${formatSize(c.size)})`);
  if (items.length > MAX_LISTED) {
    lines.push(`... and ${items.length - MAX_LISTED} more`);
  }
  return lines.join("\n");
}

/**
 * Show exactly what the dry run found and ask for consent. Higher-risk items need a
 * separate, explicit button; high-impact ones need a second confirmation on top of that.
 * Returns true only when the user agreed to remove the previewed candidates.
 */
export async function confirmClean(label: string, preview: ScanResult): Promise<boolean> {
  const items = preview.candidates;
  const higher = items.filter((c) => isHigherRisk(c.risk));
  const highImpact = items.filter((c) => c.risk === "high-impact");
  const summary = `${items.length} item(s), ${formatSize(preview.total_bytes)}`;
  const detail = `Project: ${preview.root}\n\n${describeCandidates(items)}`;

  if (higher.length === 0) {
    const pick = await vscode.window.showWarningMessage(
      `Remove ${summary} from ${label}?`,
      { modal: true, detail },
      "Remove",
    );
    return pick === "Remove";
  }

  const pick = await vscode.window.showWarningMessage(
    `Remove ${summary} from ${label}, including ${higher.length} higher-risk item(s)?`,
    {
      modal: true,
      detail:
        `Higher-risk rules are opt-in and can be slow or impossible to recreate.\n\n${detail}`,
    },
    "Remove, including higher-risk items",
  );
  if (pick === undefined) {
    return false;
  }
  if (highImpact.length === 0) {
    return true;
  }
  const second = await vscode.window.showWarningMessage(
    `${highImpact.length} high-impact item(s) will be removed. Are you sure?`,
    { modal: true, detail: describeCandidates(highImpact) },
    "Yes, remove high-impact items",
  );
  return second !== undefined;
}
