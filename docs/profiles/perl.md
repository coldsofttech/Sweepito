# perl

[Back to all profiles](../profiles.md)

Perl: ExtUtils::MakeMaker and Module::Build

**Detected by:** `Makefile.PL`, `Build.PL`, `cpanfile`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `perl.blib` | `/blib/`, `/pm_to_blib` | `Makefile.PL`, `Build.PL` | safe | Staged build library (blib/) |
| `perl.build-dir` | `/_build/` | `Build.PL` | safe | Module::Build state |
| `perl.mymeta` | `/MYMETA.json`, `/MYMETA.yml` | `Makefile.PL`, `Build.PL` | safe | Generated build metadata |

## Configuration

```toml
[clean]
enable = ["perl.blib"]
```

Command-line equivalent:

```bash
sweepito clean -p perl
```

Notes:

- Targets are the generated outputs of `perl Makefile.PL` and `perl Build.PL`: `blib/`, `pm_to_blib`, `_build/` and `MYMETA.*`.
- `Makefile` is not targeted, since it may be hand-written.
