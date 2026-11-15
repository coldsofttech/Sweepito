# Profiles and rules

A **profile** is one technology (Python, Node, Rust, ...) and holds the cleanup rules for it.
The profiles are defined in `src/sweepito/profiles/*.toml`, and each one has its own page
below. Run `sweepito rules` for the same list in the terminal, or
`sweepito rules --explain RULE_ID` for one rule.

## How profiles work

- With the default `profiles = ["auto"]`, a profile is active when one of its marker files
  exists in the project. `common` is always active.
- Use `-p NAME` (repeatable) or `profiles = [...]` in the config to choose profiles
  explicitly. That replaces auto-detection.
- A **rule** belongs to one profile and has a risk level:

| Level | Behavior |
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
language. See the [configuration guide](guides/configuration.md) for every key.

```toml
[defaults]
profiles = ["auto"]        # or a list such as ["rust", "node"]
risk = "safe"              # custom | safe | configurable | high-impact: highest level to include

[clean]
enable = ["rust.target"]   # opt in to individual rules (any risk level)
disable = ["python.hypothesis"]   # always wins over enable
exclude = ["vendor/", "dist/"]    # gitignore-style; always wins over every rule
```

`exclude` matches a candidate **or any directory above it**. `exclude = ["legacy/"]` protects
everything under `legacy/`, while `exclude = ["target/debug/"]` does not stop `target/` from
being a candidate. Command-line options are combined with these lists. Scalars such as
`--risk` override the file.

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

Custom rules follow the same safety gates as built-in ones.

## Profiles

| Profile | Detected by | Rules | Safe | Configurable | High-impact |
|---|---|---:|---:|---:|---:|
| [`batchvault`](profiles/batchvault.md) | `batchvault.toml` | 2 | 0 | 2 | 0 |
| [`clojure`](profiles/clojure.md) | `project.clj`, `deps.edn` | 2 | 2 | 0 | 0 |
| [`commitrocket`](profiles/commitrocket.md) | `commitrocket.toml`, `.commitrocketignore` | 1 | 1 | 0 | 0 |
| [`common`](profiles/common.md) | always active | 5 | 2 | 3 | 0 |
| [`cpp`](profiles/cpp.md) | `CMakeLists.txt`, `Makefile`, `build.ninja`, `meson.build` | 7 | 1 | 6 | 0 |
| [`dart`](profiles/dart.md) | `pubspec.yaml` | 3 | 0 | 3 | 0 |
| [`data-eng`](profiles/data-eng.md) | `dbt_project.yml`, `build.sbt` | 4 | 2 | 0 | 2 |
| [`docker`](profiles/docker.md) | `Dockerfile`, `compose.yaml`, `compose.yml`, `docker-compose.yaml`, `docker-compose.yml`, `.devcontainer/devcontainer.json`, `.devcontainer.json`, `skaffold.yaml` | 1 | 0 | 1 | 0 |
| [`dotnet`](profiles/dotnet.md) | `*.csproj`, `*.fsproj`, `*.vbproj`, `*.sln` | 5 | 1 | 4 | 0 |
| [`elixir`](profiles/elixir.md) | `mix.exs` | 6 | 3 | 2 | 1 |
| [`go`](profiles/go.md) | `go.mod`, `go.work` | 5 | 3 | 1 | 1 |
| [`godot`](profiles/godot.md) | `project.godot` | 1 | 1 | 0 | 0 |
| [`haskell`](profiles/haskell.md) | `*.cabal`, `stack.yaml` | 2 | 1 | 1 | 0 |
| [`jupyter`](profiles/jupyter.md) | `*.ipynb`, `dvc.yaml`, `MLproject` | 5 | 1 | 1 | 3 |
| [`jvm`](profiles/jvm.md) | `build.sbt`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`, `settings.gradle.kts` | 7 | 3 | 4 | 0 |
| [`node-pm`](profiles/node-pm.md) | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `bun.lock` | 3 | 0 | 1 | 2 |
| [`node`](profiles/node.md) | `package.json` | 22 | 12 | 9 | 1 |
| [`ocaml`](profiles/ocaml.md) | `dune-project` | 1 | 1 | 0 | 0 |
| [`perl`](profiles/perl.md) | `Makefile.PL`, `Build.PL`, `cpanfile` | 3 | 3 | 0 | 0 |
| [`php`](profiles/php.md) | `composer.json`, `artisan` | 7 | 2 | 4 | 1 |
| [`python`](profiles/python.md) | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | 20 | 8 | 10 | 2 |
| [`r`](profiles/r.md) | `DESCRIPTION`, `*.Rproj`, `renv.lock` | 6 | 1 | 3 | 2 |
| [`ruby`](profiles/ruby.md) | `Gemfile`, `config/application.rb` | 7 | 2 | 3 | 2 |
| [`rust`](profiles/rust.md) | `Cargo.toml` | 2 | 0 | 2 | 0 |
| [`swift`](profiles/swift.md) | `Package.swift`, `*.xcodeproj/project.pbxproj`, `Podfile` | 4 | 0 | 3 | 1 |
| [`terraform`](profiles/terraform.md) | `*.tf`, `terragrunt.hcl` | 5 | 1 | 4 | 0 |
| [`unity`](profiles/unity.md) | `ProjectSettings/ProjectVersion.txt` | 3 | 2 | 1 | 0 |
| [`unreal`](profiles/unreal.md) | `*.uproject` | 2 | 0 | 2 | 0 |
| **Total** | | **141** | **53** | **70** | **18** |

Each page in `docs/profiles/` lists its rules with their targets, markers and risk, an example
configuration and the notes about what is never targeted.
