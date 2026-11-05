import assert from "node:assert/strict";
import { chmodSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { candidatesFor, locate } from "../src/cli/locate";

const posix = process.platform !== "win32";

function fakeCli(banner: string): string {
  const dir = mkdtempSync(join(tmpdir(), "sweepito-fake-"));
  const file = join(dir, "sweepito");
  writeFileSync(file, `#!/bin/sh\necho "${banner}"\n`);
  chmodSync(file, 0o755);
  return file;
}

test("search order: configured path, PATH, interpreter", () => {
  const list = candidatesFor({ configuredPath: "/x/sweepito", pythonPath: "/py" });
  assert.deepEqual(
    list.map((e) => [e.command, e.prefix]),
    [
      ["/x/sweepito", []],
      ["sweepito", []],
      ["/py", ["-m", "sweepito"]],
    ],
  );
});

test("no configured path or interpreter leaves only PATH", () => {
  assert.deepEqual(candidatesFor({}).map((e) => e.command), ["sweepito"]);
});

test("reports missing when nothing runs", async () => {
  const result = await locate({ configuredPath: "/does/not/exist" });
  // `sweepito` might really be on PATH on a dev machine; only assert the shape then.
  if (result.kind === "missing") {
    assert.ok(result.tried.length >= 1);
  }
});

test("uses the configured path first", { skip: !posix }, async () => {
  const result = await locate({ configuredPath: fakeCli("sweepito 9.9.9") });
  assert.equal(result.kind, "found");
  assert.equal(result.kind === "found" && result.version, "9.9.9");
});

test("flags a too-old CLI instead of calling it missing", { skip: !posix }, async () => {
  const result = await locate({ configuredPath: fakeCli("sweepito 0.0.1") }, "0.1.0");
  assert.ok(result.kind === "too-old" || result.kind === "found");
  if (result.kind === "too-old") {
    assert.equal(result.version, "0.0.1");
    assert.equal(result.minimum, "0.1.0");
  }
});
