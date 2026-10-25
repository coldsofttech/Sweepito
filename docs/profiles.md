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


## Summary

| Profile | Detected by | Rules | Safe | Configurable | High-impact |
|---|---|---:|---:|---:|---:|
| [`common`](#common) | always active | 5 | 2 | 3 | 0 |
| [`cpp`](#cpp) | `CMakeLists.txt`, `Makefile`, `build.ninja`, `meson.build` | 6 | 1 | 5 | 0 |
| [`dart`](#dart) | `pubspec.yaml` | 3 | 0 | 3 | 0 |
| [`dotnet`](#dotnet) | `*.csproj`, `*.fsproj`, `*.vbproj`, `*.sln` | 5 | 1 | 4 | 0 |
| [`elixir`](#elixir) | `mix.exs` | 6 | 3 | 2 | 1 |
| [`go`](#go) | `go.mod`, `go.work` | 3 | 1 | 1 | 1 |
| [`jupyter`](#jupyter) | `*.ipynb`, `dvc.yaml`, `MLproject` | 5 | 1 | 1 | 3 |
| [`jvm`](#jvm) | `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`, `settings.gradle.kts` | 5 | 1 | 4 | 0 |
| [`node-pm`](#node-pm) | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `bun.lock` | 2 | 0 | 1 | 1 |
| [`node`](#node) | `package.json` | 15 | 8 | 6 | 1 |
| [`php`](#php) | `composer.json`, `artisan` | 7 | 2 | 4 | 1 |
| [`python`](#python) | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | 13 | 6 | 6 | 1 |
| [`r`](#r) | `DESCRIPTION`, `*.Rproj`, `renv.lock` | 6 | 1 | 3 | 2 |
| [`ruby`](#ruby) | `Gemfile`, `config/application.rb` | 6 | 2 | 3 | 1 |
| [`rust`](#rust) | `Cargo.toml` | 2 | 0 | 2 | 0 |
| [`swift`](#swift) | `Package.swift`, `*.xcodeproj/project.pbxproj`, `Podfile` | 4 | 0 | 3 | 1 |
| [`terraform`](#terraform) | `*.tf`, `terragrunt.hcl` | 4 | 1 | 3 | 0 |
| **Total** | | **97** | **30** | **54** | **13** |

## common

OS and editor artifacts that apply to any project

**Detected by:** always active

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `common.os-junk` | `.DS_Store`, `Thumbs.db`, `desktop.ini` | - | safe | Operating system metadata files |
| `common.pm-logs` | `npm-debug.log*`, `yarn-error.log*`, `pnpm-debug.log*` | - | safe | Package manager debug logs |
| `common.editor-temp` | `*.swp`, `*.swo`, `*~` | - | configurable | Editor swap files (may hold unsaved recovery data) |
| `common.merge-leftovers` | `*.orig`, `*.rej` | - | configurable | Merge and patch leftovers |
| `common.logs` | `*.log` | - | configurable | Generic log files |

### Configuration

```toml
[clean]
enable  = ["common.logs", "common.editor-temp"]
disable = ["common.os-junk"]
```

Command-line equivalent:

```bash
sweepito clean --enable common.logs
```

Notes:

- Always active, even without markers, and applies to every project.
- `*.log` is `configurable` because logs are sometimes intentional.
- Editor swap files can hold unsaved recovery data, so `common.editor-temp` is opt-in.
- IDE settings (`.idea/`, `.vscode/`) and `.env*` files are never targeted.

## cpp

C and C++: CMake, Make, Ninja, Meson

**Detected by:** `CMakeLists.txt`, `Makefile`, `build.ninja`, `meson.build`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `cpp.clangd` | `.cache/clangd/` | `CMakeLists.txt`, `Makefile`, `build.ninja`, `meson.build` | safe | clangd index |
| `cpp.cmake-build` | `cmake-build-*/` | `CMakeLists.txt` | configurable | CLion build directories |
| `cpp.build` | `/build/` | `CMakeLists.txt`, `meson.build`, `build.ninja` | configurable | Out-of-source build directory |
| `cpp.cmake-in-source` | `/CMakeCache.txt`, `/CMakeFiles/` | `CMakeLists.txt` | configurable | In-source CMake build leftovers |
| `cpp.objects` | `*.o`, `*.obj`, `*.a` | `CMakeLists.txt`, `Makefile`, `build.ninja`, `meson.build` | configurable | Object files and static libraries |
| `cpp.ninja` | `/.ninja_log`, `/.ninja_deps` | `build.ninja` | configurable | Ninja logs |

### Configuration

```toml
[clean]
enable  = ["cpp.build", "cpp.cmake-build"]
exclude = ["third_party/"]

# Extra build directories named build-debug, build-release, ...
[[rule]]
id = "custom.cpp-build-dirs"
paths = ["/build-*/"]
requires = ["CMakeLists.txt"]
```

Command-line equivalent:

```bash
sweepito clean -p cpp --enable cpp.build --enable cpp.cmake-build
```

Notes:

- `cpp.build` needs `CMakeLists.txt`, `meson.build` or `build.ninja` beside it.
- `cpp.objects` (`*.o`, `*.obj`, `*.a`) is pattern based, so it only removes files that git ignores.
- A Makefile alone activates the profile but does not satisfy `cpp.build`.

## dart

Dart and Flutter

**Detected by:** `pubspec.yaml`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `dart.tool` | `/.dart_tool/` | `pubspec.yaml` | configurable | Dart tool cache (pub get regenerates) |
| `dart.build` | `/build/` | `pubspec.yaml` | configurable | Flutter build output |
| `dart.legacy` | `/.packages`, `/.flutter-plugins`, `/.flutter-plugins-dependencies` | `pubspec.yaml` | configurable | Generated plugin and package files |

### Configuration

```toml
[clean]
enable = ["dart.tool", "dart.build"]
```

Command-line equivalent:

```bash
sweepito clean -p dart --enable dart.tool --enable dart.build
```

Notes:

- `dart.tool` is regenerated by `pub get`; `dart.build` is Flutter build output.
- iOS and macOS `Pods/` belong to the `swift` profile (`xcode.pods`, `high-impact`).

## dotnet

.NET: C#, F#, ASP.NET Core

**Detected by:** `*.csproj`, `*.fsproj`, `*.vbproj`, `*.sln`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `dotnet.testresults` | `TestResults/` | `*.csproj`, `*.fsproj`, `*.vbproj`, `*.sln` | safe | Test run output |
| `dotnet.bin-obj` | `/bin/`, `/obj/` | `*.csproj`, `*.fsproj`, `*.vbproj` | configurable | Build and intermediate output |
| `dotnet.artifacts` | `/artifacts/` | `Directory.Build.props`, `*.sln` | configurable | Centralised build artifacts |
| `dotnet.vs` | `/.vs/` | `*.sln` | configurable | Visual Studio per-user state |
| `dotnet.publish` | `/publish/` | `*.csproj`, `*.fsproj` | configurable | dotnet publish output |

### Configuration

```toml
[clean]
enable  = ["dotnet.bin-obj", "dotnet.publish"]
disable = ["dotnet.vs"]   # leave Visual Studio per-user state alone
```

Command-line equivalent:

```bash
sweepito clean -p dotnet --enable dotnet.bin-obj
```

Notes:

- `bin/` and `obj/` are only matched beside a `*.csproj`, `*.fsproj` or `*.vbproj`, because those names are generic.
- `dotnet.testresults` (`TestResults/`) is `safe` and matches at any depth.
- NuGet's global package cache is out of scope.

## elixir

Elixir: Mix and Phoenix

**Detected by:** `mix.exs`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `elixir.ls` | `/.elixir_ls/` | `mix.exs` | safe | ElixirLS cache |
| `elixir.crash` | `erl_crash.dump` | `mix.exs` | safe | Erlang crash dumps |
| `elixir.cover` | `/cover/` | `mix.exs` | safe | Coverage reports |
| `elixir.build` | `/_build/` | `mix.exs` | configurable | Mix build output |
| `phoenix.static` | `/priv/static/` | `mix.exs` | configurable | Phoenix compiled assets (tracked files are protected) |
| `elixir.deps` | `/deps/` | `mix.exs` | high-impact | Mix dependencies |

### Configuration

```toml
[clean]
enable = ["elixir.build", "phoenix.static"]
```

Command-line equivalent:

```bash
sweepito clean -p elixir --enable elixir.build
```

Notes:

- `phoenix.static` removes `priv/static/` only when it is git-ignored and untracked, so committed static assets are safe.
- `deps/` is `high-impact` and needs `mix deps.get` afterwards.

## go

Go modules and build tools

**Detected by:** `go.mod`, `go.work`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `go.test-artifacts` | `*.test`, `*.prof`, `coverage.out` | `go.mod`, `go.work` | safe | Compiled test binaries and profiles |
| `go.bin` | `/bin/` | `go.mod`, `go.work` | configurable | Conventional project build output |
| `go.vendor` | `/vendor/` | `go.mod`, `go.work` | high-impact | Vendored dependencies (often committed; tracked files are protected) |

### Configuration

```toml
[clean]
enable = ["go.bin"]
```

Command-line equivalent:

```bash
sweepito clean -p go --enable go.bin
```

Notes:

- `vendor/` is `high-impact` and often committed. Tracked files are protected, so a committed `vendor/` is never touched.
- The Go build and module caches are global; use `go clean -cache` for those. Sweepito does not manage them.

## jupyter

Jupyter notebooks and ML workflow outputs

**Detected by:** `*.ipynb`, `dvc.yaml`, `MLproject`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `jupyter.checkpoints` | `.ipynb_checkpoints/` | `*.ipynb` | safe | Notebook autosave checkpoints |
| `ml.lightning-logs` | `/lightning_logs/`, `/catboost_info/` | `pyproject.toml`, `requirements.txt`, `setup.py`, `*.ipynb` | configurable | Training logs |
| `ml.mlruns` | `/mlruns/` | `pyproject.toml`, `requirements.txt`, `setup.py`, `*.ipynb`, `MLproject` | high-impact | MLflow experiment history |
| `ml.wandb` | `/wandb/` | `pyproject.toml`, `requirements.txt`, `setup.py`, `*.ipynb` | high-impact | Weights & Biases local runs (may be unsynced) |
| `ml.dvc-cache` | `/.dvc/cache/` | `dvc.yaml` | high-impact | Local copies of DVC-tracked data |

### Configuration

```toml
[clean]
enable  = ["ml.lightning-logs"]
exclude = ["experiments/baseline/"]   # keep results for a finished experiment
```

Command-line equivalent:

```bash
sweepito clean -p jupyter --enable ml.lightning-logs
```

Notes:

- `jupyter.checkpoints` (`.ipynb_checkpoints/`) is `safe`.
- Experiment data is `high-impact`: `ml.mlruns`, `ml.wandb` (may be unsynced) and `ml.dvc-cache` (local copies of tracked data).
- ML rules need a Python project marker or an `*.ipynb` file.

## jvm

Java and JVM: Maven, Gradle, Kotlin, Spring Boot

**Detected by:** `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`, `settings.gradle.kts`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `jvm.kotlin` | `/.kotlin/` | `build.gradle`, `build.gradle.kts` | safe | Kotlin compiler session data |
| `jvm.maven-target` | `/target/` | `pom.xml` | configurable | Maven build output |
| `jvm.gradle-project` | `/.gradle/` | `settings.gradle`, `settings.gradle.kts`, `build.gradle`, `build.gradle.kts` | configurable | Project-level Gradle cache (not ~/.gradle) |
| `jvm.gradle-build` | `/build/` | `build.gradle`, `build.gradle.kts` | configurable | Gradle build output |
| `jvm.idea-out` | `/out/` | `*.iml` | configurable | IntelliJ default output directory |

### Configuration

```toml
[clean]
enable  = ["jvm.maven-target", "jvm.gradle-build"]
exclude = ["legacy-module/"]
```

Command-line equivalent:

```bash
sweepito clean -p jvm --enable jvm.maven-target --enable jvm.gradle-build
```

Notes:

- `jvm.maven-target` needs `pom.xml`; `jvm.gradle-build` and `jvm.kotlin` need `build.gradle` or `build.gradle.kts`; `jvm.idea-out` needs an `*.iml` file.
- `jvm.gradle-project` removes the project-level `.gradle/` only, never `~/.gradle`.
- Spring Boot output lives in the Maven or Gradle build directories above.

## node-pm

npm, pnpm, Yarn and Bun project-local stores

**Detected by:** `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `bun.lock`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `node-pm.yarn-cache` | `/.yarn/cache/` | `yarn.lock` | configurable | Yarn offline cache (skipped automatically when tracked) |
| `node-pm.pnpm-store` | `/.pnpm-store/` | `pnpm-lock.yaml` | high-impact | Local pnpm content-addressable store |

### Configuration

```toml
[clean]
enable = ["node-pm.yarn-cache"]
```

Command-line equivalent:

```bash
sweepito clean -p node-pm --enable node-pm.yarn-cache
```

Notes:

- Yarn zero-install repositories commit `.yarn/cache`. Tracked files are never removed, so that cache is skipped automatically.
- The pnpm store (`.pnpm-store/`) is `high-impact`.
- Global package manager caches (`~/.npm`, `~/.cache/yarn`) are out of scope.

## node

Node.js, React, Next.js, Vue, Nuxt, Angular, Vite, Svelte, Astro

**Detected by:** `package.json`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `node.eslint` | `.eslintcache` | `package.json` | safe | ESLint cache |
| `node.tsbuildinfo` | `*.tsbuildinfo` | `package.json` | safe | TypeScript incremental build info |
| `node.modules-cache` | `node_modules/.cache/` | `package.json` | safe | Babel, webpack and ESLint caches inside node_modules |
| `node.vite` | `.vite/` | `package.json` | safe | Vite cache |
| `node.turbo` | `.turbo/` | `package.json` | safe | Turborepo local cache |
| `node.parcel` | `.parcel-cache/` | `package.json` | safe | Parcel cache |
| `node.angular-cache` | `.angular/cache/` | `angular.json` | safe | Angular CLI cache |
| `node.astro` | `.astro/` | `astro.config.*` | safe | Astro generated types and cache |
| `node.next` | `/.next/` | `next.config.*` | configurable | Next.js build output |
| `node.nuxt` | `/.nuxt/`, `/.output/` | `nuxt.config.*` | configurable | Nuxt build output |
| `node.svelte-kit` | `/.svelte-kit/` | `svelte.config.*` | configurable | SvelteKit generated output |
| `node.dist` | `/dist/` | `package.json` | configurable | Build and distribution output |
| `node.build` | `/build/`, `/out/` | `package.json` | configurable | Build output and static exports |
| `node.coverage` | `/coverage/` | `package.json` | configurable | Test coverage reports |
| `node.modules` | `/node_modules/` | `package.json` | high-impact | Installed dependencies (requires reinstall) |

### Configuration

```toml
[clean]
enable  = ["node.next", "node.dist", "node.build"]   # framework build output
exclude = ["apps/legacy-admin/"]                      # a project you want untouched

[[rule]]
id = "custom.storybook"
paths = ["/storybook-static/"]
requires = ["package.json"]
```

Command-line equivalent:

```bash
sweepito clean -p node --enable node.next --enable node.nuxt
```

Notes:

- Framework rules need their config file: `node.next` needs `next.config.*`, `node.nuxt` needs `nuxt.config.*`, `node.svelte-kit` needs `svelte.config.*`, `node.astro` needs `astro.config.*` and `node.angular-cache` needs `angular.json`.
- Monorepos work per package: each directory with its own `package.json` and config is matched separately.
- `node.modules` (`node_modules/`) is `high-impact` and needs `--enable node.modules`. `node_modules/.cache` is a separate `safe` rule.
- When both are selected, `node_modules/` replaces its `.cache` child in the plan.

## php

PHP: Composer, Laravel, Symfony

**Detected by:** `composer.json`, `artisan`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `php.phpunit` | `.phpunit.cache/`, `.phpunit.result.cache` | `composer.json`, `artisan` | safe | PHPUnit caches |
| `php.tool-caches` | `.php-cs-fixer.cache`, `.phpstan.cache` | `composer.json`, `artisan` | safe | Code style and static analysis caches |
| `laravel.cache` | `/storage/framework/cache/`, `/storage/framework/views/`, `/bootstrap/cache/*.php` | `artisan` | configurable | Laravel framework caches (never storage/app) |
| `laravel.logs` | `/storage/logs/` | `artisan` | configurable | Laravel logs |
| `symfony.cache` | `/var/cache/` | `symfony.lock` | configurable | Symfony cache |
| `symfony.logs` | `/var/log/` | `symfony.lock` | configurable | Symfony logs |
| `php.vendor` | `/vendor/` | `composer.json` | high-impact | Composer dependencies |

### Configuration

```toml
[clean]
enable = ["laravel.cache", "symfony.cache"]
```

Command-line equivalent:

```bash
sweepito clean -p php --enable laravel.cache
```

Notes:

- Laravel rules need `artisan`; Symfony rules need `symfony.lock`.
- `storage/app` (uploads) is never targeted.
- `laravel.logs` and `symfony.logs` are opt-in because logs may be needed.
- `vendor/` (`php.vendor`) is `high-impact`.

## python

Python, Django, Flask, FastAPI, pytest, Ruff, mypy, tox, coverage

**Detected by:** `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `python.pycache` | `__pycache__/`, `*.pyc`, `*.pyo` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Bytecode caches |
| `python.pytest` | `.pytest_cache/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | pytest cache |
| `python.ruff` | `.ruff_cache/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Ruff cache |
| `python.mypy` | `.mypy_cache/`, `.dmypy.json` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | mypy cache |
| `python.typecheckers` | `.pyre/`, `.pytype/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Pyre and pytype caches |
| `python.coverage` | `.coverage`, `.coverage.*`, `htmlcov/`, `coverage.xml` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Coverage data and reports |
| `python.hypothesis` | `.hypothesis/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | Hypothesis example database (holds regression seeds) |
| `python.tox` | `.tox/`, `.nox/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | tox and nox environments |
| `python.eggs` | `.eggs/`, `*.egg-info/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | Setuptools build metadata |
| `python.build` | `/build/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | Build output |
| `python.dist` | `/dist/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | Distribution artifacts |
| `django.static` | `/staticfiles/` | `manage.py` | configurable | Django collectstatic output |
| `python.venv` | `/.venv/`, `/venv/`, `/env/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | high-impact | Virtual environments |

### Configuration

```toml
[clean]
enable  = ["python.build", "python.dist", "python.tox"]   # opt in to build output
disable = ["python.coverage"]                             # keep coverage reports
exclude = ["docs/_build/", "examples/legacy/"]            # directories to leave alone

# Custom rule for a project-specific scratch folder
[[rule]]
id = "custom.pytest-tmp"
paths = ["/.tmp-tests/"]
requires = ["pyproject.toml"]
```

Command-line equivalent:

```bash
sweepito clean -p python --enable python.build --enable python.dist
```

Notes:

- Virtual environments (`python.venv`) are `high-impact`: `sweepito clean --enable python.venv`.
- `db.sqlite3` and Flask `instance/` hold application data and are never targeted.
- `python.hypothesis` is opt-in because the example database stores failing cases that act as regression seeds.
- `build/` and `dist/` are anchored: they only match beside a Python marker such as `pyproject.toml`.

## r

R, Shiny, renv, RMarkdown

**Detected by:** `DESCRIPTION`, `*.Rproj`, `renv.lock`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `r.rcheck` | `*.Rcheck/` | `DESCRIPTION`, `*.Rproj`, `renv.lock` | safe | R CMD check output |
| `r.rproj-user` | `/.Rproj.user/` | `*.Rproj` | configurable | RStudio per-user state |
| `r.knitr-cache` | `*_cache/`, `*_files/` | `*.Rmd`, `*.qmd` | configurable | knitr and RMarkdown caches and figures |
| `r.history` | `/.Rhistory` | `DESCRIPTION`, `*.Rproj`, `renv.lock` | configurable | R command history |
| `r.rdata` | `/.RData` | `DESCRIPTION`, `*.Rproj`, `renv.lock` | high-impact | Saved workspace (may hold unsaved work) |
| `r.renv-library` | `/renv/library/` | `renv.lock` | high-impact | renv project library |

### Configuration

```toml
[clean]
enable = ["r.knitr-cache", "r.rproj-user"]
```

Command-line equivalent:

```bash
sweepito clean -p r --enable r.knitr-cache
```

Notes:

- `r.knitr-cache` matches `*_cache/` and `*_files/` and needs an `*.Rmd` or `*.qmd` file; the git-ignore check keeps unrelated folders safe.
- `.RData` is `high-impact` because it can hold unsaved work.
- `renv/library/` is `high-impact`; `renv.lock` is never touched.

## ruby

Ruby: Bundler, Rails, Sinatra

**Detected by:** `Gemfile`, `config/application.rb`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `ruby.yard` | `/.yardoc/` | `Gemfile` | safe | YARD documentation cache |
| `ruby.coverage` | `/coverage/` | `Gemfile` | safe | SimpleCov reports |
| `rails.tmp-cache` | `/tmp/cache/` | `config/application.rb` | configurable | Rails Bootsnap and asset caches |
| `rails.tmp` | `/tmp/pids/`, `/tmp/sockets/` | `config/application.rb` | configurable | Stale PID files and sockets |
| `rails.logs` | `/log/*.log` | `config/application.rb` | configurable | Rails logs |
| `ruby.vendor-bundle` | `/vendor/bundle/` | `Gemfile` | high-impact | Bundled gems (requires reinstall) |

### Configuration

```toml
[clean]
enable = ["rails.tmp-cache", "rails.logs"]
```

Command-line equivalent:

```bash
sweepito clean -p ruby --enable rails.tmp-cache
```

Notes:

- Rails rules need `config/application.rb`.
- `rails.tmp` removes stale PID files and sockets that can block server start.
- `vendor/bundle/` is `high-impact` and needs `bundle install` afterwards.

## rust

Rust and Cargo

**Detected by:** `Cargo.toml`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `rust.target` | `/target/` | `Cargo.toml` | configurable | Cargo build output (slow to rebuild) |
| `rust.profiling` | `flamegraph.svg`, `perf.data`, `perf.data.*` | `Cargo.toml` | configurable | Profiling output |

### Configuration

```toml
[clean]
enable  = ["rust.target"]
exclude = ["tools/benchmarks/"]   # keep expensive-to-rebuild benchmark workspaces
```

Command-line equivalent:

```bash
sweepito clean -p rust --enable rust.target
```

Notes:

- `target/` can reach several GB and takes minutes to rebuild, so it is `configurable` rather than `safe`.
- Cargo workspaces share one `target/` at the workspace root; it is matched beside the `Cargo.toml` that contains it.
- `~/.cargo` registry caches are global and out of scope.

## swift

Swift Package Manager and Xcode

**Detected by:** `Package.swift`, `*.xcodeproj/project.pbxproj`, `Podfile`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `swift.build` | `/.build/` | `Package.swift` | configurable | SwiftPM build output |
| `swift.swiftpm` | `/.swiftpm/` | `Package.swift` | configurable | SwiftPM and Xcode package state |
| `xcode.xcuserdata` | `xcuserdata/` | `*.xcodeproj/project.pbxproj` | configurable | Per-user Xcode state |
| `xcode.pods` | `/Pods/` | `Podfile` | high-impact | CocoaPods dependencies (requires pod install) |

### Configuration

```toml
[clean]
enable = ["swift.build", "xcode.xcuserdata"]
```

Command-line equivalent:

```bash
sweepito clean -p swift --enable swift.build
```

Notes:

- Xcode projects are detected through `*.xcodeproj/project.pbxproj`.
- `~/Library/Developer/Xcode/DerivedData` is global and out of scope.
- `Pods/` is `high-impact` and needs `pod install` afterwards.

## terraform

Terraform and Terragrunt (state files and lock files are never cleaned)

**Detected by:** `*.tf`, `terragrunt.hcl`

### Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `terraform.crash-log` | `crash.log`, `crash.*.log` | `*.tf` | safe | Terraform crash logs |
| `terraform.plans` | `*.tfplan`, `tfplan` | `*.tf` | configurable | Saved plans (a plan may be awaiting apply) |
| `terraform.dir` | `/.terraform/` | `*.tf` | configurable | Provider plugins (terraform init required again) |
| `terragrunt.cache` | `/.terragrunt-cache/` | `terragrunt.hcl` | configurable | Terragrunt module cache |

### Configuration

```toml
[clean]
enable = ["terraform.dir", "terragrunt.cache"]
```

Command-line equivalent:

```bash
sweepito clean -p terraform --enable terraform.dir
```

Notes:

- State files (`*.tfstate`, `*.tfstate.backup`) and `.terraform.lock.hcl` are never targeted by any rule.
- `terraform.dir` removes provider plugins, so `terraform init` must run again.
- `terraform.plans` is opt-in because a saved plan may be awaiting apply.
