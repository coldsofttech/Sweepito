# Sweepito for VS Code

[![CI](https://github.com/coldsofttech/Sweepito/actions/workflows/ci.yml/badge.svg)](https://github.com/coldsofttech/Sweepito/actions/workflows/ci.yml)
[![VS Code 1.90+](https://img.shields.io/badge/VS%20Code-1.90%2B-007ACC?logo=visualstudiocode&logoColor=white)](https://code.visualstudio.com/)
[![License](https://img.shields.io/github/license/coldsofttech/Sweepito)](https://github.com/coldsofttech/Sweepito/blob/main/LICENSE)

Free up disk space by cleaning caches and build output that your projects can regenerate,
without leaving the editor. Sweepito only ever removes files that Git ignores, so your source
code and anything tracked by Git is never touched.

It runs natively inside VS Code. You do not need Python or the Sweepito command line tool.
You only need Git and VS Code 1.90 or later.

## What you get

- **Cleanup candidates view.** Open the Sweepito icon in the activity bar to see what can be
  cleaned, grouped by technology, then by rule, with the size of each item. Use the buttons in
  the view title to expand or collapse everything.
- **Status bar.** Shows how much space can be reclaimed. Click it to scan again.
- **Command Palette.** Run **Sweepito: Scan**, **Sweepito: Clean**, **Sweepito: Check**,
  **Sweepito: Report** or **Sweepito: Doctor**.
- **Your own rules.** Add rules and technologies in settings or in a `sweepito.toml`.
- **Git hook.** Clean or report automatically on every commit.

## Getting started

1. Open a folder that is a Git repository.
2. Open the Sweepito view. The workspace is scanned for you.
3. Review the list, then clean what you want.

By default only the safest items are listed. Run **Sweepito: Choose Risk Level for This
Session** to see larger artifacts, such as build output that takes time to rebuild.

## Safety

- Only git-ignored files are removed. Tracked files and anything inside `.git` are skipped.
- In an untrusted workspace Sweepito can scan but not clean.
- Sweepito sends nothing over the network.

## Learn more

Every command, all settings, custom rules, the Git hook and the pre-commit framework are
covered in the [full guide](https://github.com/coldsofttech/Sweepito/blob/main/extensions/vscode/docs/vscode.md).

## Links

- [Sweepito on GitHub](https://github.com/coldsofttech/Sweepito)
- [Changelog](https://github.com/coldsofttech/Sweepito/blob/main/extensions/vscode/CHANGELOG.md)
- [Report an issue](https://github.com/coldsofttech/Sweepito/issues)
