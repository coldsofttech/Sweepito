import { spawnSync } from "node:child_process";
import { context } from "esbuild";

const production = process.argv.includes("--production");
const watch = process.argv.includes("--watch");

const profiles = spawnSync(process.execPath, ["scripts/build.mjs"], {
    stdio: "inherit",
});
if (profiles.status !== 0) process.exit(profiles.status ?? 1);

const common = {
    bundle: true,
    platform: "node",
    format: "cjs",
    target: "node18",
    minify: production,
    sourcemap: !production,
};

const contexts = [
    // The extension itself.
    await context({ ...common, entryPoints: ["src/extension.js"], outfile: "dist/extension.js", external: ["vscode"] }),
    // The script an installed Git hook runs when the sweepito command is not available.
    await context({ ...common, entryPoints: ["src/hook-cli.js"], outfile: "dist/sweepito-hook.js", sourcemap: false }),
];

if (watch) {
    await Promise.all(contexts.map((ctx) => ctx.watch()));
} else {
    for (const ctx of contexts) {
        await ctx.rebuild();
        await ctx.dispose();
    }
}
