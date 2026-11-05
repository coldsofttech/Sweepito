import * as vscode from "vscode";
import type { Selection } from "../cli/args";
import type { Risk } from "../cli/types";

/** Read the per-folder settings and turn them into a CLI selection. */
export function selectionFor(
  folder: vscode.WorkspaceFolder,
  sessionRisk?: Risk,
): Selection {
  const cfg = vscode.workspace.getConfiguration("sweepito", folder.uri);
  const configured = cfg.get<string>("configFile", "").trim();
  const inspect = cfg.inspect<string>("risk");
  // Only pass --risk when the user chose one (or this session overrides it). Otherwise the
  // CLI applies sweepito.toml / [tool.sweepito], and finally its own default (safe).
  const explicit =
    inspect?.workspaceFolderValue ?? inspect?.workspaceValue ?? inspect?.globalValue;
  return {
    risk: sessionRisk ?? (explicit as Risk | undefined),
    enable: cfg.get<string[]>("enableRules", []),
    disable: cfg.get<string[]>("disableRules", []),
    exclude: cfg.get<string[]>("exclude", []),
    configFile: configured || undefined,
  };
}

export function autoScanEnabled(): boolean {
  return vscode.workspace.getConfiguration("sweepito").get<boolean>("autoScan", true);
}

export function statusBarEnabled(): boolean {
  return vscode.workspace
    .getConfiguration("sweepito")
    .get<boolean>("statusBar.enabled", true);
}

export function configuredExecutable(): string | undefined {
  if (!vscode.workspace.isTrusted) {
    return undefined;
  }
  const value = vscode.workspace.getConfiguration("sweepito").get<string>("executablePath", "");
  return value.trim() || undefined;
}
