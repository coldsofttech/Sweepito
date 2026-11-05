import * as vscode from "vscode";
import type { Located } from "../cli/locate";

const INSTALL_COMMANDS = {
  pipx: "pipx install sweepito",
  uv: "uv tool install sweepito",
  pip: "python -m pip install --user sweepito",
} as const;

const UPGRADE_COMMANDS = {
  pipx: "pipx upgrade sweepito",
  uv: "uv tool upgrade sweepito",
  pip: "python -m pip install --user --upgrade sweepito",
} as const;

const OPEN_SETTINGS = "Open Settings";
const COPY = "Copy Command";

/**
 * Explain a missing or too-old CLI. Nothing is installed without a click, and the command
 * runs in a visible terminal so the user sees what happens.
 */
export async function explainProblem(located: Located): Promise<void> {
  if (located.kind === "found") {
    return;
  }
  const upgrade = located.kind === "too-old";
  const commands = upgrade ? UPGRADE_COMMANDS : INSTALL_COMMANDS;
  const message = upgrade
    ? `Sweepito ${located.version} is too old for this extension (needs ${located.minimum} or newer).`
    : "The Sweepito command line tool was not found. It needs Python 3.11 or newer.";
  const choice = await vscode.window.showErrorMessage(
    message,
    { detail: `Install with one of:\n  ${commands.pipx}\n  ${commands.uv}\n  ${commands.pip}` },
    upgrade ? "Upgrade with pipx" : "Install with pipx",
    upgrade ? "Upgrade with uv" : "Install with uv",
    COPY,
    OPEN_SETTINGS,
  );
  switch (choice) {
    case "Install with pipx":
    case "Upgrade with pipx":
      runInTerminal(commands.pipx);
      break;
    case "Install with uv":
    case "Upgrade with uv":
      runInTerminal(commands.uv);
      break;
    case COPY:
      await vscode.env.clipboard.writeText(commands.pipx);
      void vscode.window.showInformationMessage(`Copied: ${commands.pipx}`);
      break;
    case OPEN_SETTINGS:
      await vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "sweepito.executablePath",
      );
      break;
  }
}

function runInTerminal(command: string): void {
  const terminal = vscode.window.createTerminal("Sweepito install");
  terminal.show();
  terminal.sendText(command);
  void vscode.window.showInformationMessage(
    "When the install finishes, run Sweepito: Scan to continue.",
  );
}
