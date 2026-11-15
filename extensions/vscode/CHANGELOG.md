# Changelog

All notable changes to the Sweepito VS Code extension are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-11-15

### Added

- Cleanup candidates view in the activity bar, grouped by technology and rule, with the size of
  each item. Clean everything, one technology, one rule or a single item, or reveal it in the
  file explorer. Expand or collapse the whole tree from the view title.
- Status bar item showing the space you can reclaim. Click it to scan again.
- Scan, Clean, Check and Report commands, with the result available as JSON to open or copy.
- Native scanning and cleaning that needs only Git: no Python and no Sweepito command line tool.
- Built-in profiles for the same technologies as the command line tool, with commands to list
  and explain rules and profiles.
- Risk levels: only the safest items are listed by default, and you can choose a higher level for
  the session or in settings. Turn individual rules on or off, or exclude paths with
  gitignore-style patterns.
- Custom rules and profiles from VS Code settings or a `sweepito.toml` file, plus commands to
  create, show and validate the configuration.
- Doctor command that checks your setup and configuration. A gear button in the view title opens a
  menu with Scan, Clean, the risk level, Doctor, Check, Report and the configuration, hook and
  output commands.
- Git hook that cleans or reports on every commit, with commands to install, remove and check it.
- Sweepito output channel and terminal, with quiet and colour settings.
- Settings to confirm before cleaning, scan automatically when a workspace opens, and show or hide
  the status bar item.

### Security

- Only files that Git ignores are removed; tracked files and the `.git` folder are never touched.
- Cleaning is disabled in untrusted workspaces, where Sweepito can still scan.
- Nothing is sent over the network.
