// @ts-check
import * as vscode from "vscode";

/**
 * The last scan of each workspace folder, in folder order.
 * @type {Map<string, { name: string, root: string, plan: any, error: string | null, descriptions: Map<string, string> }>}
 */
export const states = new Map();
/** The last clean in each folder this session: { plan, result }. */
export const lastClean = new Map();
export const changed = new vscode.EventEmitter();

/**
 * Mutable extension state shared by the command modules. A property on one object, since an
 * imported `let` cannot be reassigned from another module.
 * @type {{
 *   sessionRisk: string | null,
 *   scanning: boolean,
 *   checkFlagged: boolean,
 *   extensionPath: string,
 *   extensionVersion: string,
 *   statusBar: vscode.StatusBarItem | undefined,
 *   output: vscode.OutputChannel | undefined,
 *   terminal: vscode.Terminal | undefined,
 *   terminalWriter: vscode.EventEmitter<string> | undefined,
 * }}
 */
export const state = {
    /** Risk chosen for this session; overrides the setting until the window reloads. */
    sessionRisk: null,
    scanning: false,
    /** Set by Check while items remain, so the status bar keeps a warning colour. */
    checkFlagged: false,
    extensionPath: "",
    extensionVersion: "unknown",
    statusBar: undefined,
    output: undefined,
    /** The extension-owned terminal, once opened, and the emitter that feeds it. */
    terminal: undefined,
    terminalWriter: undefined,
};

export const folders = () => vscode.workspace.workspaceFolders ?? [];
export const entries = () =>
    folders().map(
        (f) =>
            states.get(f.uri.fsPath) ?? {
                name: f.name,
                root: f.uri.fsPath,
                plan: null,
                error: null,
                descriptions: new Map(),
            },
    );
export const allCandidates = () => entries().flatMap((e) => e.plan?.candidates ?? []);

/** The message of a caught value, which TypeScript types as `unknown`. */
export const errorMessage = (/** @type {unknown} */ error) => (error instanceof Error ? error.message : String(error));
