/**
 * Runs the real CLI against a throwaway Git repository. This is the contract between the
 * extension and Sweepito: if a JSON field the extension reads changes, this fails.
 *
 * Needs a Sweepito CLI: set SWEEPITO_BIN to its path, or have `sweepito` on PATH.
 */
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { before, describe, test } from "node:test";
import { cleanArgs, cleanDryRunArgs, onlyRule, scanArgs, type Selection } from "../src/cli/args";
import { locate } from "../src/cli/locate";
import { SweepitoService } from "../src/service";

const sel: Selection = { enable: [], disable: [], exclude: [] };

function git(cwd: string, ...args: string[]): void {
  execFileSync("git", ["-c", "user.email=ci@example.com", "-c", "user.name=ci", ...args], {
    cwd,
    stdio: "ignore",
  });
}

function fixture(): string {
  const root = mkdtempSync(join(tmpdir(), "sweepito-fixture-"));
  git(root, "init", "-q");
  writeFileSync(join(root, ".gitignore"), "__pycache__/\n.pytest_cache/\n.mypy_cache/\n");
  writeFileSync(join(root, "pyproject.toml"), "[project]\nname = 'x'\n");
  writeFileSync(join(root, "keep.py"), "print('hi')\n");
  mkdirSync(join(root, "src", "__pycache__"), { recursive: true });
  writeFileSync(join(root, "src", "__pycache__", "a.pyc"), "x".repeat(100));
  mkdirSync(join(root, ".pytest_cache"));
  writeFileSync(join(root, ".pytest_cache", "v"), "y".repeat(10));
  mkdirSync(join(root, ".mypy_cache"));
  writeFileSync(join(root, ".mypy_cache", "m"), "z");
  git(root, "add", ".gitignore", "pyproject.toml", "keep.py");
  git(root, "commit", "-qm", "init");
  return root;
}

describe("sweepito CLI contract", async () => {
  const located = await locate({ configuredPath: process.env.SWEEPITO_BIN });
  const skip = located.kind === "found" ? false : "no usable sweepito CLI (set SWEEPITO_BIN)";
  let service: SweepitoService;
  before(() => {
    if (located.kind === "found") {
      service = new SweepitoService(located.exe);
    }
  });

  test("scan lists candidates with the fields the tree needs", { skip }, async () => {
    const root = fixture();
    const scan = await service.scan(root, sel);
    assert.equal(scan.dry_run, true);
    assert.ok(scan.profiles.includes("python"));
    const rules = scan.candidates.map((c) => c.rule);
    assert.ok(rules.includes("python.pycache"));
    assert.ok(rules.includes("python.pytest"));
    for (const c of scan.candidates) {
      assert.equal(typeof c.rule, "string");
      assert.equal(typeof c.profile, "string");
      assert.equal(typeof c.risk, "string");
      assert.equal(typeof c.path, "string");
      assert.equal(typeof c.is_dir, "boolean");
      assert.equal(typeof c.size, "number");
    }
    assert.equal(scan.total_bytes, scan.candidates.reduce((n, c) => n + c.size, 0));
  });

  test("the preview matches what clean then removes", { skip }, async () => {
    const root = fixture();
    const preview = await service.preview(root, sel);
    const result = await service.clean(root, sel);
    assert.deepEqual(
      result.removed.map((c) => c.path).sort(),
      preview.candidates.map((c) => c.path).sort(),
    );
    assert.equal(result.failed.length, 0);
    assert.ok(!existsSync(join(root, ".pytest_cache")));
    assert.ok(existsSync(join(root, "keep.py")), "tracked files are never touched");
    assert.equal((await service.scan(root, sel)).candidates.length, 0);
  });

  test("a rule-level clean touches only that rule", { skip }, async () => {
    const root = fixture();
    const all = (await service.rules(root)).rules.map((r) => r.id);
    const only = onlyRule(sel, "python.pytest", all);
    const result = await service.clean(root, only);
    assert.deepEqual([...new Set(result.removed.map((c) => c.rule))], ["python.pytest"]);
    assert.ok(existsSync(join(root, "src", "__pycache__")), "other rules are left alone");
  });

  test("the risk ceiling is respected without an opt-in", { skip }, async () => {
    const root = fixture();
    writeFileSync(join(root, "package.json"), "{}");
    mkdirSync(join(root, "dist"));
    writeFileSync(join(root, "dist", "o.js"), "1");
    writeFileSync(join(root, ".gitignore"), "__pycache__/\n.pytest_cache/\n.mypy_cache/\ndist/\n");
    const safe = await service.scan(root, sel);
    assert.ok(!safe.candidates.some((c) => c.risk === "configurable"));
    const raised = await service.scan(root, { ...sel, risk: "configurable" });
    assert.ok(raised.candidates.some((c) => c.risk === "configurable"));
  });

  test("a non-git folder is a safety refusal (exit 4)", { skip }, async () => {
    const dir = mkdtempSync(join(tmpdir(), "sweepito-nogit-"));
    await assert.rejects(service.scan(dir, sel), (err: { code?: number }) => err.code === 4);
  });

  test("rules, doctor and hook status parse", { skip }, async () => {
    const root = fixture();
    assert.ok((await service.rules(root)).rules.some((r) => r.id === "python.pycache"));
    const doctor = await service.doctor(root);
    assert.equal(typeof doctor.healthy, "boolean");
    assert.ok(doctor.checks.every((c) => typeof c.name === "string" && typeof c.ok === "boolean"));
    const hooks = await service.hookStatus(root);
    assert.equal(typeof hooks["post-commit"], "boolean");
  });

  test("hook install and uninstall round trip", { skip }, async () => {
    const root = fixture();
    await service.simple(["hook", "install", root, "--stage", "post-commit"], root);
    assert.equal((await service.hookStatus(root))["post-commit"], true);
    await service.simple(["hook", "uninstall", root, "--stage", "post-commit"], root);
    assert.equal((await service.hookStatus(root))["post-commit"], false);
  });

  test("argument builders produce flags the CLI accepts", { skip }, async () => {
    const root = fixture();
    const rich: Selection = { risk: "safe", enable: ["python.pycache"], disable: [], exclude: ["src/"] };
    for (const args of [scanArgs(root, rich), cleanDryRunArgs(root, rich)]) {
      const { runJson } = await import("../src/cli/run");
      const { data } = await runJson<{ candidates: { path: string }[] }>(service.executable, args);
      assert.ok(!data.candidates.some((c) => c.path.startsWith("src/")), "exclude wins");
    }
    assert.ok(cleanArgs(root, rich).includes("--yes"));
  });
});
