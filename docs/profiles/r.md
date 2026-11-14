# r

[Back to all profiles](../profiles.md)

R, Shiny, renv, RMarkdown

**Detected by:** `DESCRIPTION`, `*.Rproj`, `renv.lock`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `r.rcheck` | `*.Rcheck/` | `DESCRIPTION`, `*.Rproj`, `renv.lock` | safe | R CMD check output |
| `r.rproj-user` | `/.Rproj.user/` | `*.Rproj` | configurable | RStudio per-user state |
| `r.knitr-cache` | `*_cache/`, `*_files/` | `*.Rmd`, `*.qmd` | configurable | knitr and RMarkdown caches and figures |
| `r.history` | `/.Rhistory` | `DESCRIPTION`, `*.Rproj`, `renv.lock` | configurable | R command history |
| `r.rdata` | `/.RData` | `DESCRIPTION`, `*.Rproj`, `renv.lock` | high-impact | Saved workspace (may hold unsaved work) |
| `r.renv-library` | `/renv/library/` | `renv.lock` | high-impact | renv project library |

## Configuration

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
