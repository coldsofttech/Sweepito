import * as vscode from "vscode";
import {
  onlyProfile,
  onlyRule,
  formatSize,
  type Selection,
} from "./cli/args";
import { locate, type Located } from "./cli/locate";
import { CliError } from "./cli/run";
import { EXIT, type Risk } from "./cli/types";
import { SweepitoService } from "./service";
import { confirmClean } from "./ui/confirm";
import { explainProblem } from "./ui/install";
import {
  autoScanEnabled,
  configuredExecutable,
  selectionFor,
  statusBarEnabled,
} from "./ui/settings";
import { CandidatesTree, type FolderState, type Node } from "./ui/tree";

const output = vscode.window.createOutputChannel("Sweepito");

export function activate(context: vscode.ExtensionContext): void {
  const app = new App(context);
  context.subscriptions.push(app, output);
  app.register();
  if (autoScanEnabled()) {
    void app.scan();
  }
}

export function deactivate(): void {}

class App implements vscode.Disposable {
  private readonly tree = new CandidatesTree();
  private readonly status = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    0,
  );
  private readonly disposables: vscode.Disposable[] = [];
  private located: Located | undefined;
  private service: SweepitoService | undefined;
  private sessionRisk: Risk | undefined;
  private scanTimer: NodeJS.Timeout | undefined;
  private running: AbortController | undefined;

  constructor(_context: vscode.ExtensionContext) {
    this.status.command = "sweepito.scan";
    this.status.name = "Sweepito";
    void vscode.commands.executeCommand("setContext", "sweepito.empty", true);
  }

  dispose(): void {
    clearTimeout(this.scanTimer);
    this.running?.abort();
    this.status.dispose();
    this.disposables.forEach((d) => d.dispose());
  }

  register(): void {
    const reg = (id: string, fn: (...args: any[]) => unknown) =>
      this.disposables.push(vscode.commands.registerCommand(id, fn));
    this.disposables.push(
      vscode.window.registerTreeDataProvider("sweepito.candidates", this.tree),
    );
    reg("sweepito.scan", () => this.scan());
    reg("sweepito.clean", () => this.cleanFromPalette());
    reg("sweepito.doctor", () => this.doctor());
    reg("sweepito.installHook", () => this.hook("install"));
    reg("sweepito.uninstallHook", () => this.hook("uninstall"));
    reg("sweepito.setRisk", () => this.chooseRisk());
    reg("sweepito.openConfig", () => this.openConfig());
    reg("sweepito.createConfig", () => this.createConfig());
    reg("sweepito.showInstallHelp", async () => {
      this.located = undefined;
      await this.ensureCli(true);
    });
    reg("sweepito.cleanFolder", (n: Node) => n.kind === "folder" && this.cleanNode(n));
    reg("sweepito.cleanProfile", (n: Node) => n.kind === "profile" && this.cleanNode(n));
    reg("sweepito.cleanRule", (n: Node) => n.kind === "rule" && this.cleanNode(n));
    reg("sweepito.reveal", (n: Node) => {
      if (n.kind === "path" && n.state.result) {
        const uri = vscode.Uri.joinPath(vscode.Uri.file(n.state.result.root), n.item.path);
        void vscode.commands.executeCommand("revealInExplorer", uri);
      }
    });

    const schedule = () => {
      if (!autoScanEnabled()) {
        return;
      }
      clearTimeout(this.scanTimer);
      this.scanTimer = setTimeout(() => void this.scan(), 3000);
    };
    const gitignore = vscode.workspace.createFileSystemWatcher("**/.gitignore");
    this.disposables.push(
      gitignore,
      gitignore.onDidChange(schedule),
      gitignore.onDidCreate(schedule),
      gitignore.onDidDelete(schedule),
      vscode.workspace.onDidSaveTextDocument(schedule),
      vscode.workspace.onDidChangeWorkspaceFolders(() => void this.scan()),
      vscode.workspace.onDidGrantWorkspaceTrust(() => {
        this.located = undefined;
        void this.scan();
      }),
      vscode.workspace.onDidChangeConfiguration((e) => {
        if (e.affectsConfiguration("sweepito.executablePath")) {
          this.located = undefined;
        }
        if (e.affectsConfiguration("sweepito")) {
          void this.scan();
        }
      }),
    );
  }

  // ---- CLI discovery ------------------------------------------------------------------

  private async pythonInterpreter(): Promise<string | undefined> {
    // A workspace interpreter can contain code, so it is only used in trusted workspaces.
    if (!vscode.workspace.isTrusted) {
      return undefined;
    }
    try {
      const ext = vscode.extensions.getExtension("ms-python.python");
      if (!ext) {
        return undefined;
      }
      const api = ext.isActive ? ext.exports : await ext.activate();
      const folder = vscode.workspace.workspaceFolders?.[0]?.uri;
      return api?.environments?.getActiveEnvironmentPath?.(folder)?.path || undefined;
    } catch {
      return undefined;
    }
  }

  private async ensureCli(forceMessage = false): Promise<SweepitoService | undefined> {
    if (!this.located) {
      this.located = await locate({
        configuredPath: configuredExecutable(),
        pythonPath: await this.pythonInterpreter(),
      });
      this.service =
        this.located.kind === "found" ? new SweepitoService(this.located.exe) : undefined;
      output.appendLine(
        this.located.kind === "found"
          ? `Using ${this.located.exe.label} (${this.located.version})`
          : this.located.kind === "too-old"
            ? `Found Sweepito ${this.located.version} at ${this.located.exe.label}, too old`
            : `Sweepito not found. Tried: ${this.located.tried.join(", ")}`,
      );
      await vscode.commands.executeCommand(
        "setContext",
        "sweepito.cliMissing",
        this.located.kind !== "found",
      );
    }
    if (this.located.kind !== "found" && forceMessage) {
      await explainProblem(this.located);
    }
    return this.service;
  }

  /** Commands the user ran explicitly show the install message; background scans stay quiet. */
  private async requireCli(): Promise<SweepitoService | undefined> {
    return this.ensureCli(true);
  }

  // ---- scanning -----------------------------------------------------------------------

  private folders(): readonly vscode.WorkspaceFolder[] {
    return (vscode.workspace.workspaceFolders ?? []).filter((f) => f.uri.scheme === "file");
  }

  async scan(): Promise<void> {
    const service = await this.ensureCli(false);
    if (!service) {
      this.tree.update([]);
      this.updateStatus();
      return;
    }
    this.running?.abort();
    const controller = new AbortController();
    this.running = controller;
    const states: FolderState[] = [];
    for (const folder of this.folders()) {
      states.push(await this.scanFolder(service, folder, controller.signal));
    }
    if (controller.signal.aborted) {
      return;
    }
    this.tree.update(states);
    await vscode.commands.executeCommand("setContext", "sweepito.empty", states.length === 0);
    this.updateStatus();
  }

  private async scanFolder(
    service: SweepitoService,
    folder: vscode.WorkspaceFolder,
    signal: AbortSignal,
  ): Promise<FolderState> {
    try {
      const result = await service.scan(
        folder.uri.fsPath,
        selectionFor(folder, this.sessionRisk),
        signal,
      );
      return { folder, result };
    } catch (err) {
      if (err instanceof CliError && err.code === EXIT.SAFETY) {
        return { folder, message: "Not a Git repository. Nothing can be verified as ignored." };
      }
      const message = err instanceof Error ? err.message : String(err);
      output.appendLine(`[${folder.name}] scan failed: ${message}`);
      return { folder, message: `Scan failed: ${message}` };
    }
  }

  private updateStatus(): void {
    if (!statusBarEnabled() || this.tree.count === 0) {
      this.status.hide();
      return;
    }
    this.status.text = `$(trash) ${formatSize(this.tree.total)}`;
    this.status.tooltip = `Sweepito: ${this.tree.count} cleanup candidate(s), ${formatSize(
      this.tree.total,
    )} reclaimable. Click to rescan.`;
    this.status.show();
  }

  // ---- cleaning -----------------------------------------------------------------------

  private requireTrust(action: string): boolean {
    if (vscode.workspace.isTrusted) {
      return true;
    }
    void vscode.window
      .showWarningMessage(
        `${action} is disabled in an untrusted workspace. Scanning still works.`,
        "Manage Workspace Trust",
      )
      .then((pick) => {
        if (pick) {
          void vscode.commands.executeCommand("workbench.trust.manage");
        }
      });
    return false;
  }

  private async cleanNode(node: Node): Promise<void> {
    if (node.kind !== "folder" && node.kind !== "profile" && node.kind !== "rule") {
      return;
    }
    const folder = node.state.folder;
    if (node.kind === "folder") {
      await this.cleanFolder(folder, (s) => s, folder.name);
    } else if (node.kind === "profile") {
      await this.cleanFolder(folder, (s) => onlyProfile(s, node.profile), `${folder.name} (${node.profile})`);
    } else {
      const service = await this.requireCli();
      if (!service) {
        return;
      }
      try {
        const all = (await service.rules(folder.uri.fsPath, selectionFor(folder).configFile)).rules;
        await this.cleanFolder(
          folder,
          (s) =>
            onlyRule(
              s,
              node.rule,
              all.map((r) => r.id),
            ),
          `${folder.name} (${node.rule})`,
        );
      } catch (err) {
        this.fail(err);
      }
    }
  }

  private async cleanFromPalette(): Promise<void> {
    if (!this.requireTrust("Clean")) {
      return;
    }
    const folder = await this.pickFolder();
    if (!folder) {
      return;
    }
    const scope = await vscode.window.showQuickPick(
      [
        {
          label: "All safe items",
          description: "Ignores the risk setting and enabled rules",
          safeOnly: true,
        },
        {
          label: "Everything the current settings select",
          description: "Uses sweepito.risk, enabled rules and sweepito.toml",
          safeOnly: false,
        },
      ],
      { title: `Sweepito: Clean ${folder.name}`, placeHolder: "What should be cleaned?" },
    );
    if (!scope) {
      return;
    }
    await this.cleanFolder(
      folder,
      (s) => (scope.safeOnly ? { ...s, risk: "safe", enable: [] } : s),
      folder.name,
    );
  }

  private async cleanFolder(
    folder: vscode.WorkspaceFolder,
    narrow: (sel: Selection) => Selection,
    label: string,
  ): Promise<void> {
    if (!this.requireTrust("Clean")) {
      return;
    }
    const service = await this.requireCli();
    if (!service) {
      return;
    }
    const root = folder.uri.fsPath;
    const sel = narrow(selectionFor(folder, this.sessionRisk));
    try {
      const preview = await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: `Sweepito: previewing ${label}` },
        () => service.preview(root, sel),
      );
      if (preview.candidates.length === 0) {
        void vscode.window.showInformationMessage(`Sweepito: nothing to clean in ${label}.`);
        return;
      }
      if (!(await confirmClean(label, preview))) {
        return;
      }
      // Same selection as the confirmed preview; only now is --yes added.
      const result = await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: `Sweepito: cleaning ${label}` },
        () => service.clean(root, sel),
      );
      output.appendLine(
        `[${label}] removed ${result.removed.length}, freed ${formatSize(result.freed_bytes)}`,
      );
      if (result.failed.length > 0) {
        for (const f of result.failed) {
          output.appendLine(`  failed: ${f.path}: ${f.error}`);
        }
        const pick = await vscode.window.showWarningMessage(
          `Sweepito removed ${result.removed.length} item(s) but ${result.failed.length} failed.`,
          "Show Details",
        );
        if (pick) {
          output.show();
        }
      } else {
        void vscode.window.showInformationMessage(
          `Sweepito: freed ${formatSize(result.freed_bytes)} (${result.removed.length} item(s)).`,
        );
      }
    } catch (err) {
      this.fail(err);
    } finally {
      void this.scan();
    }
  }

  private async chooseRisk(): Promise<void> {
    const pick = await vscode.window.showQuickPick(
      [
        { label: "Use setting", description: "sweepito.risk / sweepito.toml", value: undefined },
        { label: "safe", description: "Caches that are cheap to recreate", value: "safe" as Risk },
        {
          label: "configurable",
          description: "Build output; slower to rebuild (opt-in)",
          value: "configurable" as Risk,
        },
        {
          label: "high-impact",
          description: "Dependencies and similar; expensive to restore (opt-in)",
          value: "high-impact" as Risk,
        },
      ],
      {
        title: "Sweepito: risk level for this session",
        placeHolder: `Currently: ${this.sessionRisk ?? "from settings"}. Nothing is removed without a confirmation.`,
      },
    );
    if (pick) {
      this.sessionRisk = pick.value;
      await this.scan();
    }
  }

  // ---- doctor, hooks, config ----------------------------------------------------------

  private async pickFolder(): Promise<vscode.WorkspaceFolder | undefined> {
    const folders = this.folders();
    if (folders.length === 0) {
      void vscode.window.showWarningMessage("Sweepito: open a folder first.");
      return undefined;
    }
    if (folders.length === 1) {
      return folders[0];
    }
    const pick = await vscode.window.showWorkspaceFolderPick({
      placeHolder: "Which workspace folder?",
    });
    return pick;
  }

  private async doctor(): Promise<void> {
    const service = await this.requireCli();
    const folder = service && (await this.pickFolder());
    if (!service || !folder) {
      return;
    }
    try {
      const report = await service.doctor(
        folder.uri.fsPath,
        selectionFor(folder).configFile,
      );
      output.clear();
      output.appendLine(`Sweepito doctor for ${folder.uri.fsPath}`);
      for (const c of report.checks) {
        const state = c.ok ? "OK     " : c.required ? "FAILED " : "MISSING";
        output.appendLine(`  ${state} ${c.name.padEnd(18)} ${c.detail}`);
      }
      output.show(true);
      const failed = report.checks.filter((c) => !c.ok && c.required);
      if (report.healthy) {
        void vscode.window.showInformationMessage("Sweepito doctor: all required checks passed.");
      } else {
        void vscode.window.showWarningMessage(
          `Sweepito doctor: ${failed.map((c) => c.name).join(", ")} failed. See the Sweepito output.`,
        );
      }
    } catch (err) {
      this.fail(err);
    }
  }

  private async hook(action: "install" | "uninstall"): Promise<void> {
    if (!this.requireTrust(action === "install" ? "Installing a Git hook" : "Removing a Git hook")) {
      return;
    }
    const service = await this.requireCli();
    const folder = service && (await this.pickFolder());
    if (!service || !folder) {
      return;
    }
    const stage = await vscode.window.showQuickPick(
      [
        { label: "post-commit", description: "Clean after each commit (default)" },
        { label: "pre-commit", description: "Report only, before each commit. Never blocks a commit" },
      ],
      { title: `Sweepito: ${action} Git hook`, placeHolder: "Which hook stage?" },
    );
    if (!stage) {
      return;
    }
    try {
      const message = await service.simple(
        ["hook", action, folder.uri.fsPath, "--stage", stage.label],
        folder.uri.fsPath,
      );
      void vscode.window.showInformationMessage(`Sweepito: ${message || `${action}ed ${stage.label} hook.`}`);
    } catch (err) {
      this.fail(err);
    }
  }

  private async openConfig(): Promise<void> {
    const folder = await this.pickFolder();
    if (!folder) {
      return;
    }
    const names = ["sweepito.toml", ".sweepito.toml", "pyproject.toml"];
    for (const name of names) {
      const uri = vscode.Uri.joinPath(folder.uri, name);
      try {
        await vscode.workspace.fs.stat(uri);
      } catch {
        continue;
      }
      if (name === "pyproject.toml") {
        const text = Buffer.from(await vscode.workspace.fs.readFile(uri)).toString("utf8");
        if (!text.includes("[tool.sweepito")) {
          continue;
        }
      }
      await vscode.window.showTextDocument(uri);
      return;
    }
    const pick = await vscode.window.showInformationMessage(
      "No Sweepito config found in this folder.",
      "Create Config File",
    );
    if (pick) {
      await this.createConfig(folder);
    }
  }

  private async createConfig(folder?: vscode.WorkspaceFolder): Promise<void> {
    if (!this.requireTrust("Creating a config file")) {
      return;
    }
    const service = await this.requireCli();
    const target = service && (folder ?? (await this.pickFolder()));
    if (!service || !target) {
      return;
    }
    try {
      await service.simple(["init", target.uri.fsPath], target.uri.fsPath);
      await vscode.window.showTextDocument(vscode.Uri.joinPath(target.uri, "sweepito.toml"));
    } catch (err) {
      this.fail(err);
    }
  }

  private fail(err: unknown): void {
    const message = err instanceof Error ? err.message : String(err);
    output.appendLine(`error: ${message}`);
    void vscode.window.showErrorMessage(`Sweepito: ${message}`);
  }
}
