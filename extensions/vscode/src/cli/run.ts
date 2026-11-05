import { execFile } from "node:child_process";
import { EXIT } from "./types";

/** How to start Sweepito: a program plus leading arguments (e.g. `python -m sweepito`). */
export interface Executable {
  command: string;
  prefix: string[];
  /** Human readable form for messages. */
  label: string;
}

export interface RunResult {
  code: number;
  stdout: string;
  stderr: string;
  /** Set when the process could not be started at all (e.g. ENOENT). */
  spawnError?: string;
}

export interface RunOptions {
  cwd?: string;
  signal?: AbortSignal;
  timeoutMs?: number;
}

const MAX_OUTPUT = 64 * 1024 * 1024;

/**
 * Run the CLI without a shell, so paths and rule IDs are never interpreted by one.
 * Never rejects: failures come back as a non-zero `code` and/or `spawnError`.
 */
export function run(
  exe: Executable,
  args: string[],
  options: RunOptions = {},
): Promise<RunResult> {
  return new Promise((resolve) => {
    const child = execFile(
      exe.command,
      [...exe.prefix, ...args],
      {
        cwd: options.cwd,
        encoding: "utf8",
        maxBuffer: MAX_OUTPUT,
        timeout: options.timeoutMs ?? 10 * 60 * 1000,
        signal: options.signal,
        windowsHide: true,
        env: { ...process.env, NO_COLOR: "1", PYTHONIOENCODING: "utf-8" },
      },
      (error, stdout, stderr) => {
        if (!error) {
          resolve({ code: 0, stdout, stderr });
          return;
        }
        const err = error as NodeJS.ErrnoException & { code?: number | string };
        if (typeof err.code === "number") {
          resolve({ code: err.code, stdout, stderr });
        } else {
          resolve({
            code: -1,
            stdout: stdout ?? "",
            stderr: stderr ?? "",
            spawnError: err.code ? String(err.code) : err.message,
          });
        }
      },
    );
    child.stdin?.end();
  });
}

export class CliError extends Error {
  constructor(
    message: string,
    readonly code: number,
    readonly stderr: string,
  ) {
    super(message);
    this.name = "CliError";
  }
}

/** Strip the `sweepito: error: ` prefix the CLI puts on stderr messages. */
export function errorMessage(result: RunResult): string {
  const text = (result.stderr || result.stdout || result.spawnError || "").trim();
  const line =
    text
      .split(/\r?\n/)
      .reverse()
      .find((l) => l.trim().length > 0) ?? "";
  return line.replace(/^sweepito: error:\s*/, "") || `exit code ${result.code}`;
}

/**
 * Run a command that prints one JSON document and parse it.
 * `acceptCodes` lists exit codes that still carry a document (e.g. 1 = some items failed).
 */
export async function runJson<T>(
  exe: Executable,
  args: string[],
  options: RunOptions = {},
  acceptCodes: number[] = [EXIT.OK],
): Promise<{ data: T; code: number }> {
  const result = await run(exe, [...args, "--json"], options);
  if (!acceptCodes.includes(result.code)) {
    throw new CliError(errorMessage(result), result.code, result.stderr);
  }
  try {
    return { data: JSON.parse(result.stdout) as T, code: result.code };
  } catch {
    throw new CliError(
      "Sweepito printed output that is not valid JSON. Update the CLI or report a bug.",
      result.code,
      result.stderr,
    );
  }
}
