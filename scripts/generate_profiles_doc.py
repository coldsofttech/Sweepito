"""Generate docs/profiles.md from the built-in profiles.

Run from the repository root after changing a profile:

    uv run python scripts/generate_profiles_doc.py

The per-profile configuration examples live in ``PROFILE_DOCS`` below. They are validated
against the real config loader by tests/test_docs.py.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from sweepito.registry import Registry

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "profiles.md"

# profile id -> {"toml": config snippet, "notes": [...], "cli": example command}
PROFILE_DOCS: dict[str, dict] = {
    "python": {
        "toml": """\
[clean]
enable  = ["python.build", "python.dist", "python.tox"]   # opt in to build output
disable = ["python.coverage"]                             # keep coverage reports
exclude = ["docs/_build/", "examples/legacy/"]            # directories to leave alone

# Custom rule for a project-specific scratch folder
[[rule]]
id = "custom.pytest-tmp"
paths = ["/.tmp-tests/"]
requires = ["pyproject.toml"]
""",
        "cli": "sweepito clean -p python --enable python.build --enable python.dist",
        "notes": [
            "Virtual environments (`python.venv`) are `high-impact`: "
            "`sweepito clean --enable python.venv`.",
            "`db.sqlite3` and Flask `instance/` hold application data and are never targeted.",
            "`python.hypothesis` is opt-in because the example database stores failing "
            "cases that act as regression seeds.",
            "`build/` and `dist/` are anchored: they only match beside a Python marker "
            "such as `pyproject.toml`.",
        ],
    },
    "node": {
        "toml": """\
[clean]
enable  = ["node.next", "node.dist", "node.build"]   # framework build output
exclude = ["apps/legacy-admin/"]                      # a project you want untouched

[[rule]]
id = "custom.storybook"
paths = ["/storybook-static/"]
requires = ["package.json"]
""",
        "cli": "sweepito clean -p node --enable node.next --enable node.nuxt",
        "notes": [
            "Framework rules need their config file: `node.next` needs `next.config.*`, "
            "`node.nuxt` needs `nuxt.config.*`, `node.svelte-kit` needs `svelte.config.*`, "
            "`node.astro` needs `astro.config.*` and `node.angular-cache` needs `angular.json`.",
            "Monorepos work per package: each directory with its own `package.json` and "
            "config is matched separately.",
            "`node.modules` (`node_modules/`) is `high-impact` and needs "
            "`--enable node.modules`. `node_modules/.cache` is a separate `safe` rule.",
            "When both are selected, `node_modules/` replaces its `.cache` child in the plan.",
        ],
    },
    "node-pm": {
        "toml": """\
[clean]
enable = ["node-pm.yarn-cache"]
""",
        "cli": "sweepito clean -p node-pm --enable node-pm.yarn-cache",
        "notes": [
            "Yarn zero-install repositories commit `.yarn/cache`. Tracked files are never "
            "removed, so that cache is skipped automatically.",
            "The pnpm store (`.pnpm-store/`) is `high-impact`.",
            "Global package manager caches (`~/.npm`, `~/.cache/yarn`) are out of scope.",
        ],
    },
    "rust": {
        "toml": """\
[clean]
enable  = ["rust.target"]
exclude = ["tools/benchmarks/"]   # keep expensive-to-rebuild benchmark workspaces
""",
        "cli": "sweepito clean -p rust --enable rust.target",
        "notes": [
            "`target/` can reach several GB and takes minutes to rebuild, so it is "
            "`configurable` rather than `safe`.",
            "Cargo workspaces share one `target/` at the workspace root; it is matched "
            "beside the `Cargo.toml` that contains it.",
            "`~/.cargo` registry caches are global and out of scope.",
        ],
    },
    "jvm": {
        "toml": """\
[clean]
enable  = ["jvm.maven-target", "jvm.gradle-build"]
exclude = ["legacy-module/"]
""",
        "cli": "sweepito clean -p jvm --enable jvm.maven-target --enable jvm.gradle-build",
        "notes": [
            "`jvm.maven-target` needs `pom.xml`; `jvm.gradle-build` and `jvm.kotlin` need "
            "`build.gradle` or `build.gradle.kts`; `jvm.idea-out` needs an `*.iml` file.",
            "`jvm.gradle-project` removes the project-level `.gradle/` only, never "
            "`~/.gradle`.",
            "Spring Boot output lives in the Maven or Gradle build directories above.",
        ],
    },
    "dotnet": {
        "toml": """\
[clean]
enable  = ["dotnet.bin-obj", "dotnet.publish"]
disable = ["dotnet.vs"]   # leave Visual Studio per-user state alone
""",
        "cli": "sweepito clean -p dotnet --enable dotnet.bin-obj",
        "notes": [
            "`bin/` and `obj/` are only matched beside a `*.csproj`, `*.fsproj` or "
            "`*.vbproj`, because those names are generic.",
            "`dotnet.testresults` (`TestResults/`) is `safe` and matches at any depth.",
            "NuGet's global package cache is out of scope.",
        ],
    },
    "go": {
        "toml": """\
[clean]
enable = ["go.bin"]
""",
        "cli": "sweepito clean -p go --enable go.bin",
        "notes": [
            "`vendor/` is `high-impact` and often committed. Tracked files are protected, "
            "so a committed `vendor/` is never touched.",
            "The Go build and module caches are global; use `go clean -cache` for those. "
            "Sweepito does not manage them.",
        ],
    },
    "cpp": {
        "toml": """\
[clean]
enable  = ["cpp.build", "cpp.cmake-build"]
exclude = ["third_party/"]

# Extra build directories named build-debug, build-release, ...
[[rule]]
id = "custom.cpp-build-dirs"
paths = ["/build-*/"]
requires = ["CMakeLists.txt"]
""",
        "cli": "sweepito clean -p cpp --enable cpp.build --enable cpp.cmake-build",
        "notes": [
            "`cpp.build` needs `CMakeLists.txt`, `meson.build` or `build.ninja` beside it.",
            "`cpp.objects` (`*.o`, `*.obj`, `*.a`) is pattern based, so it only removes "
            "files that git ignores.",
            "A Makefile alone activates the profile but does not satisfy `cpp.build`.",
        ],
    },
    "php": {
        "toml": """\
[clean]
enable = ["laravel.cache", "symfony.cache"]
""",
        "cli": "sweepito clean -p php --enable laravel.cache",
        "notes": [
            "Laravel rules need `artisan`; Symfony rules need `symfony.lock`.",
            "`storage/app` (uploads) is never targeted.",
            "`laravel.logs` and `symfony.logs` are opt-in because logs may be needed.",
            "`vendor/` (`php.vendor`) is `high-impact`.",
        ],
    },
    "ruby": {
        "toml": """\
[clean]
enable = ["rails.tmp-cache", "rails.logs"]
""",
        "cli": "sweepito clean -p ruby --enable rails.tmp-cache",
        "notes": [
            "Rails rules need `config/application.rb`.",
            "`rails.tmp` removes stale PID files and sockets that can block server start.",
            "`vendor/bundle/` is `high-impact` and needs `bundle install` afterwards.",
        ],
    },
    "dart": {
        "toml": """\
[clean]
enable = ["dart.tool", "dart.build"]
""",
        "cli": "sweepito clean -p dart --enable dart.tool --enable dart.build",
        "notes": [
            "`dart.tool` is regenerated by `pub get`; `dart.build` is Flutter build output.",
            "iOS and macOS `Pods/` belong to the `swift` profile (`xcode.pods`, "
            "`high-impact`).",
        ],
    },
    "swift": {
        "toml": """\
[clean]
enable = ["swift.build", "xcode.xcuserdata"]
""",
        "cli": "sweepito clean -p swift --enable swift.build",
        "notes": [
            "Xcode projects are detected through `*.xcodeproj/project.pbxproj`.",
            "`~/Library/Developer/Xcode/DerivedData` is global and out of scope.",
            "`Pods/` is `high-impact` and needs `pod install` afterwards.",
        ],
    },
    "elixir": {
        "toml": """\
[clean]
enable = ["elixir.build", "phoenix.static"]
""",
        "cli": "sweepito clean -p elixir --enable elixir.build",
        "notes": [
            "`phoenix.static` removes `priv/static/` only when it is git-ignored and "
            "untracked, so committed static assets are safe.",
            "`deps/` is `high-impact` and needs `mix deps.get` afterwards.",
        ],
    },
    "r": {
        "toml": """\
[clean]
enable = ["r.knitr-cache", "r.rproj-user"]
""",
        "cli": "sweepito clean -p r --enable r.knitr-cache",
        "notes": [
            "`r.knitr-cache` matches `*_cache/` and `*_files/` and needs an `*.Rmd` or "
            "`*.qmd` file; the git-ignore check keeps unrelated folders safe.",
            "`.RData` is `high-impact` because it can hold unsaved work.",
            "`renv/library/` is `high-impact`; `renv.lock` is never touched.",
        ],
    },
    "jupyter": {
        "toml": """\
[clean]
enable  = ["ml.lightning-logs"]
exclude = ["experiments/baseline/"]   # keep results for a finished experiment
""",
        "cli": "sweepito clean -p jupyter --enable ml.lightning-logs",
        "notes": [
            "`jupyter.checkpoints` (`.ipynb_checkpoints/`) is `safe`.",
            "Experiment data is `high-impact`: `ml.mlruns`, `ml.wandb` (may be unsynced) "
            "and `ml.dvc-cache` (local copies of tracked data).",
            "ML rules need a Python project marker or an `*.ipynb` file.",
        ],
    },
    "terraform": {
        "toml": """\
[clean]
enable = ["terraform.dir", "terragrunt.cache"]
""",
        "cli": "sweepito clean -p terraform --enable terraform.dir",
        "notes": [
            "State files (`*.tfstate`, `*.tfstate.backup`) and `.terraform.lock.hcl` are "
            "never targeted by any rule.",
            "`terraform.dir` removes provider plugins, so `terraform init` must run again.",
            "`terraform.plans` is opt-in because a saved plan may be awaiting apply.",
        ],
    },
    "common": {
        "toml": """\
[clean]
enable  = ["common.logs", "common.editor-temp"]
disable = ["common.os-junk"]
""",
        "cli": "sweepito clean --enable common.logs",
        "notes": [
            "Always active, even without markers, and applies to every project.",
            "`*.log` is `configurable` because logs are sometimes intentional.",
            "Editor swap files can hold unsaved recovery data, so `common.editor-temp` "
            "is opt-in.",
            "IDE settings (`.idea/`, `.vscode/`) and `.env*` files are never targeted.",
        ],
    },
}

INTRO = """\
# Profiles and rules

Generated from the built-in profile files in `src/sweepito/profiles/` by
`scripts/generate_profiles_doc.py`. Run `sweepito rules` for the same list, or
`sweepito rules --explain RULE_ID` for one rule.

## How profiles work

- A **profile** is a technology. With the default `profiles = ["auto"]`, a profile is
  active when one of its marker files exists in the project. `common` is always active.
- Use `-p NAME` (repeatable) or `profiles = [...]` in the config to choose profiles
  explicitly. That replaces auto-detection.
- A **rule** belongs to one profile and has a risk level:

| Level | Behaviour |
|---|---|
| `safe` | On by default |
| `configurable` | Opt-in: `enable = [...]`, `--enable RULE`, or a higher `risk` |
| `high-impact` | Opt-in: `--enable RULE`, `enable = [...]`, or `--risk high-impact` |
| `custom` | Rules you define yourself: always on; `--risk custom` selects only these |

- A **target** starting with `/` is anchored to the directory that contains the marker file.
  Other patterns match at any depth below it. Every target must also be git-ignored and
  untracked.
- **Requires** lists the marker files a rule needs. Without its marker, the rule never fires.
  A rule with no `requires` uses its profile's markers.

## Configuring any profile

Settings live in `sweepito.toml` (or `[tool.sweepito]` in `pyproject.toml`), the same for every
language:

```toml
[defaults]
profiles = ["auto"]        # or a list such as ["rust", "node"]
risk = "safe"              # custom | safe | configurable | high-impact: highest level to include

[clean]
enable  = ["rust.target"]  # opt in to individual rules (any risk level)
disable = ["python.hypothesis"]   # always wins over enable
exclude = ["vendor/", "dist/"]    # gitignore-style; always wins over every rule
```

`exclude` matches a candidate **or any directory above it**. `exclude = ["legacy/"]` protects
everything under `legacy/`, while `exclude = ["target/debug/"]` does not stop `target/` from being
a candidate. Command-line options are combined with these lists. Scalars such as `--risk` override
the file.

### Custom profiles and rules

```toml
[profile.team]                       # a profile active when one of its markers exists
markers = ["team.marker"]

[[rule]]
id = "team.build-output"
profile = "team"
paths = ["/out/", "/.cache/gen/"]
requires = ["team.marker"]           # optional; defaults to the profile's markers
```

Custom rules follow the same safety gates as built-in ones. Details are in
[configuration.md](configuration.md).

"""


def render() -> str:
    registry = Registry.build()
    out = [INTRO, "## Summary\n"]
    out.append("| Profile | Detected by | Rules | Safe | Configurable | High-impact |")
    out.append("|---|---|---:|---:|---:|---:|")
    for profile in registry.profiles.values():
        counts = Counter(rule.risk.label for rule in profile.rules)
        markers = (
            ", ".join(f"`{m}`" for m in profile.markers)
            if profile.markers
            else "always active"
        )
        out.append(
            f"| [`{profile.id}`](#{profile.id}) | {markers} | {len(profile.rules)} | "
            f"{counts['safe']} | {counts['configurable']} | {counts['high-impact']} |"
        )
    total = Counter(rule.risk.label for rule in registry.rules.values())
    out.append(
        f"| **Total** | | **{len(registry.rules)}** | **{total['safe']}** | "
        f"**{total['configurable']}** | **{total['high-impact']}** |"
    )
    out.append("")
    for profile in registry.profiles.values():
        docs = PROFILE_DOCS[profile.id]
        out.append(f"## {profile.id}\n")
        out.append(f"{profile.description}\n")
        out.append(
            "**Detected by:** "
            + (
                ", ".join(f"`{m}`" for m in profile.markers)
                if profile.markers
                else "always active"
            )
            + "\n"
        )
        out.append("### Rules\n")
        out.append("| Rule ID | Targets | Requires | Risk | Description |")
        out.append("|---|---|---|---|---|")
        for rule in profile.rules:
            requires = ", ".join(f"`{m}`" for m in (rule.requires or profile.markers))
            paths = ", ".join(f"`{p}`" for p in rule.paths)
            out.append(
                f"| `{rule.id}` | {paths} | {requires or '-'} | {rule.risk.label} | "
                f"{rule.description} |"
            )
        out.append("")
        out.append("### Configuration\n")
        out.append("```toml\n" + docs["toml"].rstrip() + "\n```\n")
        out.append("Command-line equivalent:\n")
        out.append(f"```bash\n{docs['cli']}\n```\n")
        out.append("Notes:\n")
        out.extend(f"- {note}" for note in docs["notes"])
        out.append("")
    return "\n".join(out)


def main() -> None:
    OUTPUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
