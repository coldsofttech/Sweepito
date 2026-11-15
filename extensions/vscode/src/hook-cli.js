// Entry point of dist/sweepito-hook.js, the script a Git hook runs when the sweepito command
// is not installed. It does not import vscode.
import { runHook } from "./core/hookRun";

runHook(process.argv.slice(2), process.cwd()).then((code) => process.exit(code));
