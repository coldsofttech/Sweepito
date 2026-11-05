import assert from "node:assert/strict";
import { test } from "node:test";
import {
  cleanArgs,
  cleanDryRunArgs,
  formatSize,
  isHigherRisk,
  onlyProfile,
  onlyRule,
  scanArgs,
  type Selection,
} from "../src/cli/args";

const base: Selection = { enable: [], disable: [], exclude: [] };

test("scan with no settings passes no selection flags", () => {
  assert.deepEqual(scanArgs("/p", base), ["scan", "/p"]);
});

test("settings become flags", () => {
  const sel: Selection = {
    risk: "configurable",
    enable: ["rust.target", "rust.target"],
    disable: ["python.hypothesis"],
    exclude: ["dist/"],
    configFile: "/c.toml",
  };
  assert.deepEqual(scanArgs("/p", sel), [
    "scan", "/p", "--config", "/c.toml", "--risk", "configurable",
    "--enable", "rust.target", "--disable", "python.hypothesis", "--exclude", "dist/",
  ]);
});

test("preview is a dry run and never carries --yes", () => {
  const args = cleanDryRunArgs("/p", base);
  assert.ok(args.includes("--dry-run"));
  assert.ok(!args.includes("--yes"));
});

test("clean carries --yes and the same selection as the preview", () => {
  const sel: Selection = { ...base, risk: "safe", exclude: ["keep/"] };
  const preview = cleanDryRunArgs("/p", sel).filter((a) => a !== "--dry-run");
  const real = cleanArgs("/p", sel).filter((a) => a !== "--yes");
  assert.deepEqual(real, preview);
});

test("onlyRule enables the target and disables every other rule", () => {
  const sel = onlyRule(
    { ...base, disable: ["a.x"] },
    "a.y",
    ["a.x", "a.y", "b.z"],
  );
  assert.deepEqual(sel.enable, ["a.y"]);
  assert.deepEqual(sel.disable, ["a.x", "b.z"]);
});

test("onlyRule overrides a user disable of the target", () => {
  const sel = onlyRule({ ...base, disable: ["a.y"] }, "a.y", ["a.y"]);
  assert.deepEqual(sel.disable, []);
});

test("onlyProfile restricts profiles", () => {
  assert.deepEqual(scanArgs("/p", onlyProfile(base, "node")), [
    "scan", "/p", "--profile", "node",
  ]);
});

test("risk helpers", () => {
  assert.equal(isHigherRisk("safe"), false);
  assert.equal(isHigherRisk("custom"), false);
  assert.equal(isHigherRisk("configurable"), true);
  assert.equal(isHigherRisk("high-impact"), true);
});

test("formatSize matches the CLI", () => {
  assert.equal(formatSize(11), "11 B");
  assert.equal(formatSize(4966), "4.8 KB");
  assert.equal(formatSize(1024 * 1024), "1.0 MB");
});
