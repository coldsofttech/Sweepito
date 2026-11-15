// @ts-check
import * as vscode from "vscode";
import { styles } from "./core/terminal";
import { state } from "./state";

/**
 * Writes to the output channel unless `sweepito.quiet` is on (errors always go through).
 * @param {string} text
 * @param {{ error?: boolean }} [options]
 */
export function log(text, { error = false } = {}) {
    if (!error && vscode.workspace.getConfiguration("sweepito").get("quiet", false)) return;
    state.output?.appendLine(text);
}

/** Opens (or reveals) the Sweepito terminal, an extension-owned tab with no shell. */
export function showTerminal() {
    if (!state.terminal || state.terminal.exitStatus !== undefined) {
        state.terminalWriter?.dispose();
        /** @type {vscode.EventEmitter<string>} */
        const writer = new vscode.EventEmitter();
        state.terminalWriter = writer;
        state.terminal = vscode.window.createTerminal({
            name: "Sweepito",
            pty: {
                onDidWrite: writer.event,
                open: () =>
                    writer.fire("Sweepito results appear here. Turn colour off with sweepito.terminal.color.\r\n"),
                close: () => {},
                handleInput: () => {},
            },
        });
    }
    state.terminal.show(true);
}

/**
 * Prints to the Sweepito terminal, but only once the user has opened it.
 * @param {(c: ReturnType<typeof styles>) => string} render
 */
export function toTerminal(render) {
    if (!state.terminal || state.terminal.exitStatus !== undefined || !state.terminalWriter) return;
    const color = vscode.workspace.getConfiguration("sweepito").get("terminal.color", true);
    // Terminals need CRLF line endings.
    state.terminalWriter.fire(`${render(styles(color)).replace(/\r?\n/g, "\r\n")}\r\n\r\n`);
}

/** URI scheme of the read-only documents behind the Markdown results. */
export const DOCUMENT_SCHEME = "sweepito-doc";
/** Content of each open result, by document path. */
const documents = new Map();
const documentsChanged = new vscode.EventEmitter();

/** @type {vscode.TextDocumentContentProvider & vscode.Disposable} */
export const documentProvider = {
    onDidChange: documentsChanged.event,
    provideTextDocumentContent: (uri) => documents.get(uri.path) ?? "",
    dispose: () => documentsChanged.dispose(),
};

/**
 * Shows Markdown as a rendered preview in a single tab. The text lives in a read-only document that
 * is not shown, so there is no editor tab and nothing to save. Showing the same result again (a
 * result has the same title each time) refreshes the open tab.
 * @param {string} content
 */
export async function showMarkdown(content) {
    const title = content.match(/^#\s+(.+)$/m)?.[1] ?? "Sweepito";
    const path = `/${title.replace(/[\\/:*?"<>|]/g, "-")}.md`;
    documents.set(path, content);
    const uri = vscode.Uri.from({ scheme: DOCUMENT_SCHEME, path });
    documentsChanged.fire(uri);
    await vscode.commands.executeCommand("markdown.showPreview", uri);
}

/**
 * Opens text as a JSON document.
 * @param {unknown} value
 */
export async function showJson(value) {
    const doc = await vscode.workspace.openTextDocument({
        language: "json",
        content: `${JSON.stringify(value, null, 2)}\n`,
    });
    await vscode.window.showTextDocument(doc, { preview: true });
}
