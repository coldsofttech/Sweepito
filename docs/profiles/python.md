# python

[Back to all profiles](../profiles.md)

Python, Django, Flask, FastAPI, pytest, Ruff, mypy, Pylint, tox, coverage, Sphinx, MkDocs, Pixi, PDM

**Detected by:** `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `python.pycache` | `__pycache__/`, `*.pyc`, `*.pyo` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Bytecode caches |
| `python.pytest` | `.pytest_cache/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | pytest cache |
| `python.ruff` | `.ruff_cache/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Ruff cache |
| `python.mypy` | `.mypy_cache/`, `.dmypy.json` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | mypy cache |
| `python.pylint` | `.pylint.d/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Pylint stats |
| `python.typecheckers` | `.pyre/`, `.pytype/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Pyre and pytype caches |
| `python.sphinx` | `/_build/` | `conf.py` | safe | Sphinx documentation build output |
| `python.coverage` | `.coverage`, `.coverage.*`, `htmlcov/`, `coverage.xml` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | safe | Coverage data and reports |
| `python.mkdocs` | `/site/` | `mkdocs.yml` | configurable | MkDocs build output (could be a published folder) |
| `python.pdm` | `/.pdm-python`, `/.pdm-build/` | `pdm.lock` | configurable | PDM interpreter pointer and build cache |
| `python.hypothesis` | `.hypothesis/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | Hypothesis example database (holds regression seeds) |
| `python.tox` | `.tox/`, `.nox/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | tox and nox environments |
| `python.eggs` | `.eggs/`, `*.egg-info/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | Setuptools build metadata |
| `python.build` | `/build/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | Build output |
| `python.dist` | `/dist/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | configurable | Distribution artifacts |
| `django.static` | `/staticfiles/` | `manage.py` | configurable | Django collectstatic output |
| `python.pixi` | `/.pixi/` | `pixi.toml` | high-impact | Pixi environment (costly to rebuild, may need network) |
| `python.venv` | `/.venv/`, `/venv/`, `/env/` | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `manage.py` | high-impact | Virtual environments |

## Configuration

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
- Documentation and tool rules need their own marker: `python.sphinx` (`_build/`) needs `conf.py`, `python.mkdocs` (`site/`) needs `mkdocs.yml`, `python.pixi` needs `pixi.toml` and `python.pdm` needs `pdm.lock`. Both doc folders are anchored.
- `python.mkdocs` is `configurable` because `site/` may be a published folder. `python.pixi` (`.pixi/`) is `high-impact` like `python.venv`.
- Poetry and uv use `.venv/`, covered by `python.venv`. The uv cache, PDM cache and Pyright have no project-local cache, so nothing shared or global is targeted.
