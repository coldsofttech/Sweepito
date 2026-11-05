/** Shapes of the JSON documents printed by `sweepito ... --json` (see docs/cli.md). */

export type Risk = "custom" | "safe" | "configurable" | "high-impact";

export interface Candidate {
  rule: string;
  profile: string;
  risk: Risk;
  /** Posix path relative to the project root. */
  path: string;
  is_dir: boolean;
  size: number;
}

export interface Skipped {
  path: string;
  rule: string;
  reason: string;
}

export interface ScanResult {
  root: string;
  profiles: string[];
  candidates: Candidate[];
  skipped: Skipped[];
  total_bytes: number;
  dry_run: boolean;
}

export interface Failure {
  path: string;
  error: string;
}

export interface CleanResult extends ScanResult {
  removed: Candidate[];
  failed: Failure[];
  freed_bytes: number;
}

export interface RuleInfo {
  id: string;
  profile: string;
  risk: Risk;
  default: boolean;
  description: string;
}

export interface RulesResult {
  rules: RuleInfo[];
}

export interface DoctorCheck {
  name: string;
  ok: boolean;
  detail: string;
  required: boolean;
}

export interface DoctorResult {
  healthy: boolean;
  checks: DoctorCheck[];
}

/** `hook status --json`: stage name to installed flag. */
export type HookStatus = Record<string, boolean>;

/** Exit codes documented in docs/cli.md. */
export const EXIT = {
  OK: 0,
  FAILED: 1,
  USAGE: 2,
  BUG: 3,
  SAFETY: 4,
  INTERRUPTED: 130,
} as const;
