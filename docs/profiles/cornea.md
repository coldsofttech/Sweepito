# cornea

[Back to all profiles](../profiles.md)

Cornea Shell (configuration, build recipes and the per-user window data are never touched)

**Detected by:** `cornea.toml`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `cornea.log` | `cornea.log*` | `cornea.toml` | safe | Cornea debug log and its rotated copies (recreated on the next run with --log-file) |

## Configuration

```toml
[clean]
disable = ["cornea.log"]
```

Command-line equivalent:

```bash
sweepito clean -p cornea
```

Notes:

- `cornea.log` removes `cornea.log` and its rotated copies (`cornea.log.1` to `.3`), written beside the project when `cornea open` or `cornea serve` runs with a relative `--log-file`. The only thing lost is history you might attach to a bug report, so do not clean while investigating a bug.
- Never targeted: `cornea.toml`, PyInstaller `*.spec` files, the web folder Cornea serves (`web/`, `static/`, a built `dist/`) and `.venv/`.
- `%LOCALAPPDATA%\Cornea\` (the default debug log, `window.json`, `instance.json`, `window.tmp`) and PyInstaller's `_MEI*` unpack folder are outside the project and never targeted.
- The profile is detected from `cornea.toml`; `[tool.cornea]` in `pyproject.toml` is not detectable because markers match file names only.
