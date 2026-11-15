# jupyter

[Back to all profiles](../profiles.md)

Jupyter notebooks and ML workflow outputs

**Detected by:** `*.ipynb`, `dvc.yaml`, `MLproject`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `jupyter.checkpoints` | `.ipynb_checkpoints/` | `*.ipynb` | safe | Notebook autosave checkpoints |
| `ml.lightning-logs` | `/lightning_logs/`, `/catboost_info/` | `pyproject.toml`, `requirements.txt`, `setup.py`, `*.ipynb` | high-impact | Training logs |
| `ml.mlruns` | `/mlruns/` | `pyproject.toml`, `requirements.txt`, `setup.py`, `*.ipynb`, `MLproject` | high-impact | MLflow experiment history |
| `ml.wandb` | `/wandb/` | `pyproject.toml`, `requirements.txt`, `setup.py`, `*.ipynb` | high-impact | Weights & Biases local runs (may be unsynced) |
| `ml.dvc-cache` | `/.dvc/cache/` | `dvc.yaml` | high-impact | Local copies of DVC-tracked data |

## Configuration

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
