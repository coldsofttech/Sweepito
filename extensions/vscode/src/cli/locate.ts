import { type Executable, run } from "./run";
import { isSupported, MIN_CLI_VERSION, parseVersion } from "./version";

export interface Candidate {
  exe: Executable;
}

export type Located =
  | { kind: "found"; exe: Executable; version: string }
  | { kind: "too-old"; exe: Executable; version: string; minimum: string }
  | { kind: "missing"; tried: string[] };

export interface LocateInputs {
  /** The `sweepito.executablePath` setting; pass undefined when it must be ignored. */
  configuredPath?: string;
  /** Interpreter of the active Python environment, when known and allowed. */
  pythonPath?: string;
}

export function candidatesFor(inputs: LocateInputs): Executable[] {
  const list: Executable[] = [];
  if (inputs.configuredPath?.trim()) {
    const command = inputs.configuredPath.trim();
    list.push({ command, prefix: [], label: command });
  }
  list.push({ command: "sweepito", prefix: [], label: "sweepito (PATH)" });
  if (inputs.pythonPath) {
    list.push({
      command: inputs.pythonPath,
      prefix: ["-m", "sweepito"],
      label: `${inputs.pythonPath} -m sweepito`,
    });
  }
  return list;
}

/**
 * Try the configured path, `sweepito` on PATH, then the active interpreter, in that order.
 * The first one that answers `--version` wins. A found-but-too-old CLI is remembered, so the
 * message can say so rather than claiming nothing is installed.
 */
export async function locate(
  inputs: LocateInputs,
  minimum = MIN_CLI_VERSION,
): Promise<Located> {
  const tried: string[] = [];
  let tooOld: Located | undefined;
  for (const exe of candidatesFor(inputs)) {
    tried.push(exe.label);
    const result = await run(exe, ["--version"], { timeoutMs: 15_000 });
    if (result.code !== 0) {
      continue;
    }
    const version = parseVersion(result.stdout || result.stderr);
    if (!version) {
      continue;
    }
    if (isSupported(version, minimum)) {
      return { kind: "found", exe, version };
    }
    tooOld ??= { kind: "too-old", exe, version, minimum };
  }
  return tooOld ?? { kind: "missing", tried };
}
