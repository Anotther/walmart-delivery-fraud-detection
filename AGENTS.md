# AGENTS.md

## Cursor Cloud specific instructions

This is a Python data-science project. The user-facing product is a **Streamlit
multi-page dashboard** (`dashboard/app.py`) for Walmart delivery fraud detection.
PostgreSQL, MLflow model training, and Jupyter notebooks are all optional and not
required to run or test the dashboard.

### Environment
- Dependencies are installed into a virtualenv at `.venv/` (gitignored). The
  startup update script recreates it and installs `requirements.txt` plus the dev
  tools `pytest`, `bandit`, and `pip-audit` (used by the test suite and
  `scripts/security_checks.sh`, but not pinned in `requirements.txt`).
- Always invoke tools via the venv, e.g. `.venv/bin/streamlit`,
  `.venv/bin/python -m pytest`. There is no need to `source` the venv.
- `.env` is created from `.env.example` (gitignored). The default `DATA_SOURCE=csv`
  makes the app read directly from the committed CSVs in `data/`; no database
  needed. Standard run/test commands are documented in `README.md`.

### Running the dashboard
- Run: `.venv/bin/streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true`
- Health check: `curl http://localhost:8501/_stcore/health` returns `ok`.
- Note: the entry point is `dashboard/app.py`. There is a near-identical `app.py`
  at the repo root, but the README/devcontainer/Streamlit-Cloud config all use
  `dashboard/app.py` — use that one.
- Benign startup noise to ignore: a warning that `ui.githubLink` is not a valid
  config option, and (only if `DATA_SOURCE=database` with no Postgres) a
  "Database connection failed… Fallback mode enabled" warning. Neither blocks the
  CSV-backed dashboard.

### Testing / checks
- Tests: `.venv/bin/python -m pytest tests/`. As of setup, 25 pass and 4 fail in
  `tests/test_methodology_metadata.py`. These 4 failures are a **pre-existing**
  test/code mismatch (the tests monkeypatch `src.dashboard.data_cache.load_orders`,
  which does not exist — the module uses `self._data_source.load_orders()`), not an
  environment problem. There is no CI workflow gating the test suite (only
  `.github/workflows/pages.yml` and `pdf-export.yml`).
- Security/quality: `PYTHON_BIN=.venv/bin/python bash scripts/security_checks.sh`
  runs bandit, pip-audit, and pytest. Bandit alone:
  `.venv/bin/python -m bandit -r src dashboard scripts -q`.
