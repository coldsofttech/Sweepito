"""Integration tests for the jupyter profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="jupyter",
    profile="jupyter",
    markers={
        "MLproject": "",
        "dvc.yaml": "",
        "nb.ipynb": "{}",
        "pyproject.toml": "[project]\nname='x'\n",
    },
    targets={
        "jupyter.checkpoints": ["notebooks/.ipynb_checkpoints/"],
        "ml.dvc-cache": [".dvc/cache/"],
        "ml.lightning-logs": ["lightning_logs/", "catboost_info/"],
        "ml.mlruns": ["mlruns/"],
        "ml.wandb": ["wandb/"],
    },
    blocked_without={
        "jupyter.checkpoints": ["nb.ipynb"],
        "ml.dvc-cache": ["dvc.yaml"],
        "ml.lightning-logs": ["nb.ipynb", "pyproject.toml"],
        "ml.mlruns": ["MLproject", "nb.ipynb", "pyproject.toml"],
        "ml.wandb": ["nb.ipynb", "pyproject.toml"],
    },
)

CASES = [CASE]


class TestJupyter(ProfileSuite):
    case = CASE
