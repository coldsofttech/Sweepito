import * as vscode from "vscode";
import { formatSize, isHigherRisk } from "../cli/args";
import type { Candidate, Risk, ScanResult } from "../cli/types";

export interface FolderState {
  folder: vscode.WorkspaceFolder;
  result?: ScanResult;
  /** A short explanation shown instead of results (not a git repo, config error, ...). */
  message?: string;
}

export type Node =
  | { kind: "folder"; state: FolderState }
  | { kind: "profile"; state: FolderState; profile: string; items: Candidate[] }
  | { kind: "rule"; state: FolderState; rule: string; items: Candidate[] }
  | { kind: "path"; state: FolderState; item: Candidate }
  | { kind: "message"; text: string };

const RISK_ICON: Record<Risk, vscode.ThemeIcon> = {
  custom: new vscode.ThemeIcon("symbol-misc"),
  safe: new vscode.ThemeIcon("pass", new vscode.ThemeColor("testing.iconPassed")),
  configurable: new vscode.ThemeIcon(
    "warning",
    new vscode.ThemeColor("list.warningForeground"),
  ),
  "high-impact": new vscode.ThemeIcon(
    "error",
    new vscode.ThemeColor("list.errorForeground"),
  ),
};

function sum(items: Candidate[]): number {
  return items.reduce((n, c) => n + c.size, 0);
}

function group<T>(items: T[], key: (item: T) => string): Map<string, T[]> {
  const map = new Map<string, T[]>();
  for (const item of items) {
    const k = key(item);
    (map.get(k) ?? map.set(k, []).get(k)!).push(item);
  }
  return new Map([...map.entries()].sort(([a], [b]) => a.localeCompare(b)));
}

export class CandidatesTree implements vscode.TreeDataProvider<Node> {
  private readonly emitter = new vscode.EventEmitter<Node | undefined>();
  readonly onDidChangeTreeData = this.emitter.event;
  private states: FolderState[] = [];

  update(states: FolderState[]): void {
    this.states = states;
    this.emitter.fire(undefined);
  }

  get total(): number {
    return this.states.reduce((n, s) => n + (s.result?.total_bytes ?? 0), 0);
  }

  get count(): number {
    return this.states.reduce((n, s) => n + (s.result?.candidates.length ?? 0), 0);
  }

  stateFor(folder: vscode.WorkspaceFolder): FolderState | undefined {
    return this.states.find((s) => s.folder.uri.toString() === folder.uri.toString());
  }

  getChildren(node?: Node): Node[] {
    if (!node) {
      if (this.states.length === 1) {
        return this.profilesOf(this.states[0]);
      }
      return this.states.map((state) => ({ kind: "folder", state }));
    }
    switch (node.kind) {
      case "folder":
        return this.profilesOf(node.state);
      case "profile": {
        return [...group(node.items, (c) => c.rule)].map(([rule, items]) => ({
          kind: "rule" as const,
          state: node.state,
          rule,
          items,
        }));
      }
      case "rule":
        return node.items
          .slice()
          .sort((a, b) => b.size - a.size)
          .map((item) => ({ kind: "path" as const, state: node.state, item }));
      default:
        return [];
    }
  }

  private profilesOf(state: FolderState): Node[] {
    if (state.message) {
      return [{ kind: "message", text: state.message }];
    }
    const candidates = state.result?.candidates ?? [];
    if (!state.result) {
      return [];
    }
    if (candidates.length === 0) {
      return [{ kind: "message", text: "Nothing to clean." }];
    }
    return [...group(candidates, (c) => c.profile)].map(([profile, items]) => ({
      kind: "profile" as const,
      state,
      profile,
      items,
    }));
  }

  getTreeItem(node: Node): vscode.TreeItem {
    switch (node.kind) {
      case "message":
        return new vscode.TreeItem(node.text);
      case "folder": {
        const item = new vscode.TreeItem(
          node.state.folder.name,
          vscode.TreeItemCollapsibleState.Expanded,
        );
        item.contextValue = "folder";
        item.iconPath = new vscode.ThemeIcon("root-folder");
        item.description = node.state.message
          ? ""
          : formatSize(node.state.result?.total_bytes ?? 0);
        return item;
      }
      case "profile": {
        const item = new vscode.TreeItem(
          node.profile,
          vscode.TreeItemCollapsibleState.Expanded,
        );
        item.contextValue = "profile";
        item.description = `${node.items.length} · ${formatSize(sum(node.items))}`;
        item.iconPath = new vscode.ThemeIcon("package");
        return item;
      }
      case "rule": {
        const item = new vscode.TreeItem(
          node.rule,
          vscode.TreeItemCollapsibleState.Collapsed,
        );
        const risk = node.items[0].risk;
        item.contextValue = "rule";
        item.description = `${risk} · ${formatSize(sum(node.items))}`;
        item.iconPath = RISK_ICON[risk];
        item.tooltip = isHigherRisk(risk)
          ? `${node.rule}: ${risk} risk. Removal needs explicit confirmation.`
          : node.rule;
        return item;
      }
      case "path": {
        const c = node.item;
        const item = new vscode.TreeItem(c.is_dir ? `${c.path}/` : c.path);
        item.description = formatSize(c.size);
        item.contextValue = "path";
        item.iconPath = vscode.ThemeIcon[c.is_dir ? "Folder" : "File"];
        item.resourceUri = vscode.Uri.joinPath(vscode.Uri.file(node.state.result!.root), c.path);
        item.command = {
          command: "sweepito.reveal",
          title: "Reveal in Explorer",
          arguments: [node],
        };
        return item;
      }
    }
  }
}
