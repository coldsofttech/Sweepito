import { cleanArgs, cleanDryRunArgs, scanArgs, type Selection } from "./cli/args";
import { type Executable, run, runJson, errorMessage, CliError } from "./cli/run";
import {
  EXIT,
  type CleanResult,
  type DoctorResult,
  type HookStatus,
  type RulesResult,
  type ScanResult,
} from "./cli/types";

/** Typed, vscode-free wrapper around the CLI. Every removal goes through `clean`. */
export class SweepitoService {
  constructor(private exe: Executable) {}

  get executable(): Executable {
    return this.exe;
  }

  scan(root: string, sel: Selection, signal?: AbortSignal): Promise<ScanResult> {
    return runJson<ScanResult>(this.exe, scanArgs(root, sel), { cwd: root, signal }).then(
      (r) => r.data,
    );
  }

  /** Same selection as `clean`, nothing removed. Used to build the confirmation. */
  preview(root: string, sel: Selection, signal?: AbortSignal): Promise<ScanResult> {
    return runJson<ScanResult>(this.exe, cleanDryRunArgs(root, sel), {
      cwd: root,
      signal,
    }).then((r) => r.data);
  }

  /** Only call this after the user confirmed a `preview` built from the same selection. */
  async clean(root: string, sel: Selection, signal?: AbortSignal): Promise<CleanResult> {
    const { data } = await runJson<CleanResult>(
      this.exe,
      cleanArgs(root, sel),
      { cwd: root, signal },
      [EXIT.OK, EXIT.FAILED],
    );
    return data;
  }

  async rules(root: string, configFile?: string): Promise<RulesResult> {
    const args = ["rules", root, ...(configFile ? ["--config", configFile] : [])];
    return (await runJson<RulesResult>(this.exe, args, { cwd: root })).data;
  }

  /** Exit 1 means a required check failed, but the document is still printed. */
  async doctor(root: string, configFile?: string): Promise<DoctorResult> {
    const args = ["doctor", root, ...(configFile ? ["--config", configFile] : [])];
    return (
      await runJson<DoctorResult>(this.exe, args, { cwd: root }, [EXIT.OK, EXIT.FAILED])
    ).data;
  }

  async hookStatus(root: string): Promise<HookStatus> {
    return (await runJson<HookStatus>(this.exe, ["hook", "status", root], { cwd: root })).data;
  }

  /** The hook and init commands print text only; success is the exit code. */
  async simple(args: string[], cwd: string): Promise<string> {
    const result = await run(this.exe, args, { cwd });
    if (result.code !== 0) {
      throw new CliError(errorMessage(result), result.code, result.stderr);
    }
    return (result.stdout || result.stderr).trim();
  }
}
