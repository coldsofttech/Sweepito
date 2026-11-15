// @ts-check
import * as vscode from "vscode";
import { formatSize } from "./core/models";
import { changed, entries, folders, state } from "./state";
import { childrenOf } from "./tree-model";

export function renderStatus() {
    const statusBar = state.statusBar;
    if (!statusBar) return;
    const enabled = vscode.workspace.getConfiguration("sweepito").get("statusBar.enabled", true);
    if (!enabled || folders().length === 0) {
        statusBar.hide();
        return;
    }
    const list = entries();
    const failed = list.filter((e) => e.error);
    const planned = list.filter((e) => e.plan);
    const bytes = planned.reduce((sum, e) => sum + e.plan.totalBytes, 0);
    const count = planned.reduce((sum, e) => sum + e.plan.candidates.length, 0);

    if (state.scanning) statusBar.text = "$(sync~spin) Sweepito";
    else if (failed.length) statusBar.text = `$(warning) Sweepito${planned.length ? ` ${formatSize(bytes)}` : ""}`;
    else statusBar.text = planned.length ? `$(trash) ${formatSize(bytes)}` : "$(trash) Sweepito";
    statusBar.tooltip = failed.length
        ? `Sweepito: ${failed.map((e) => `${e.name}: ${e.error}`).join("; ")} Click to retry.`
        : planned.length
          ? `Sweepito: ${count} item(s) can be cleaned. Click to rescan.`
          : "Sweepito: click to scan";
    statusBar.backgroundColor =
        state.checkFlagged && count > 0 ? new vscode.ThemeColor("statusBarItem.warningBackground") : undefined;
    statusBar.show();
}

/** @implements {vscode.TreeDataProvider<any>} */
export class CandidatesProvider {
    onDidChangeTreeData = changed.event;

    /** @param {any} node */
    getTreeItem(node) {
        const collapsible = node.expandable
            ? vscode.TreeItemCollapsibleState.Collapsed
            : vscode.TreeItemCollapsibleState.None;
        const item = new vscode.TreeItem(node.label, collapsible);
        item.description = node.description;
        item.contextValue = node.kind;
        item.tooltip = node.tooltip;
        if (node.kind === "workspace") item.iconPath = new vscode.ThemeIcon("root-folder");
        if (node.kind === "error") item.iconPath = new vscode.ThemeIcon("warning");
        if (node.kind === "folder") {
            item.iconPath = node.isDir ? vscode.ThemeIcon.Folder : vscode.ThemeIcon.File;
            item.command = { command: "sweepito.reveal", title: "Reveal", arguments: [node] };
        }
        return item;
    }

    /** @param {any} [node] */
    getChildren(node) {
        const descriptions = new Map(entries().flatMap((e) => [...e.descriptions]));
        return childrenOf(entries(), node, descriptions);
    }
}
