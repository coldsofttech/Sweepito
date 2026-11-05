import assert from "node:assert/strict";
import { test } from "node:test";
import { compareVersions, isSupported, parseVersion } from "../src/cli/version";

test("parseVersion reads the CLI banner", () => {
  assert.equal(parseVersion("sweepito 0.1.0\n"), "0.1.0");
  assert.equal(parseVersion("sweepito 1.12.3rc1"), "1.12.3");
  assert.equal(parseVersion("command not found"), undefined);
});

test("compareVersions orders numerically", () => {
  assert.ok(compareVersions("0.10.0", "0.9.0") > 0);
  assert.ok(compareVersions("0.1.0", "0.1.0") === 0);
  assert.ok(compareVersions("0.0.9", "0.1.0") < 0);
});

test("isSupported", () => {
  assert.equal(isSupported("0.1.0", "0.1.0"), true);
  assert.equal(isSupported("0.0.9", "0.1.0"), false);
});
