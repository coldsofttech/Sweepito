/** The oldest Sweepito release the extension is tested against. */
export const MIN_CLI_VERSION = "0.1.0";

/** Pull `X.Y.Z` out of `sweepito --version` output such as `sweepito 0.1.0`. */
export function parseVersion(output: string): string | undefined {
  const match = /(\d+)\.(\d+)\.(\d+)/.exec(output);
  return match ? `${match[1]}.${match[2]}.${match[3]}` : undefined;
}

/** Negative, zero or positive, like a comparator. Ignores pre-release suffixes. */
export function compareVersions(a: string, b: string): number {
  const pa = a.split(".").map((n) => parseInt(n, 10) || 0);
  const pb = b.split(".").map((n) => parseInt(n, 10) || 0);
  for (let i = 0; i < 3; i++) {
    const diff = (pa[i] ?? 0) - (pb[i] ?? 0);
    if (diff !== 0) {
      return diff;
    }
  }
  return 0;
}

export function isSupported(version: string, minimum = MIN_CLI_VERSION): boolean {
  return compareVersions(version, minimum) >= 0;
}
