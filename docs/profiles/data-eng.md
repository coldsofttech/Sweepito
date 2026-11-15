# data-eng

[Back to all profiles](../profiles.md)

Data engineering: dbt and Apache Spark (data directories are never cleaned)

**Detected by:** `dbt_project.yml`, `build.sbt`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `dbt.target` | `/target/` | `dbt_project.yml` | configurable | dbt compiled SQL and run artifacts (recreated by the next dbt command) |
| `dbt.logs` | `/logs/` | `dbt_project.yml` | safe | dbt logs (recreated by the next dbt command) |
| `dbt.packages` | `/dbt_packages/` | `dbt_project.yml` | high-impact | dbt packages (dbt deps required again, needs network) |
| `spark.warehouse` | `/spark-warehouse/` | `build.sbt` | high-impact | Spark SQL warehouse (may hold managed-table data, not just cache) |

## Configuration

```toml
[clean]
enable = ["dbt.packages"]
exclude = ["analytics/target/"]   # keep artifacts used for state comparison
```

Command-line equivalent:

```bash
sweepito clean -p data-eng --enable dbt.packages
```

Notes:

- Only the default dbt paths are targeted; `target-path` and `log-path` set in `dbt_project.yml` are not read. Add a custom rule for non-default locations.
- `dbt.target` is `configurable` because it removes `manifest.json` and `run_results.json`, which `--state` comparisons and CI may reuse.
- `dbt.packages` is `high-impact`: `dbt deps` needs network access to restore it.
- `spark.warehouse` is `high-impact` because Spark SQL managed tables store real data there; it needs `build.sbt`.
- `data/`, `warehouse/`, `models/` and experiment outputs are never targeted. Kedro has no rules: its datasets live in `data/`.
- DVC (`ml.dvc-cache`) and MLflow (`ml.mlruns`) stay in the `jupyter` profile.
