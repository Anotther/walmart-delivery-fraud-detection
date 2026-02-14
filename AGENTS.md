# Repository Guidelines

## Project Structure & Module Organization
- `src/` is the core Python package with `etl/`, `features/`, `models/`, `analysis/`, `database/`, `dashboard/`, and `utils/`.
- `dashboard/` contains the Streamlit app (`app.py`), page modules in `dashboard/pages/`, and shared UI pieces in `dashboard/components/`.
- `scripts/` holds CLI entry points for setup, ETL, training, and reports.
- `data/` stores the 2023 CSVs; `outputs/` is for generated artifacts.
- `notebooks/` contains EDA/experiments; `docs/` contains architecture, style guides, and planning notes.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` installs dependencies.
- `python scripts/setup_database.py` initializes PostgreSQL schema and loads data (reads `.env`).
- `python scripts/run_etl.py` runs the CSV-to-database ETL pipeline.
- `python scripts/train_models.py` trains ML models and risk scoring.
- `streamlit run dashboard/app.py` launches the dashboard at `http://localhost:8501`.
- `pytest tests/` runs the test suite (currently light, but standard).
- `jupyter notebook notebooks/` opens exploratory notebooks.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and clear, typed Python.
- Use `snake_case` for functions/variables and `PascalCase` for classes.
- Dashboard page files use numeric prefixes (for example, `1_Overview.py`).
- SQL files in `src/database/sql/` use ordered prefixes (for example, `001_create_schema.sql`).
- For dashboard visuals, use the shared theme and risk colors from `src/config/viz_theme.py` and follow `docs/visualization_style_guide.md`.
- Keep known data quirks intact (for example, `products_data.csv` uses `produc_id`).

## Testing Guidelines
- Use `pytest` with `test_*.py` naming in `tests/`.
- Add tests for new ETL transforms, feature calculations, or model helpers when feasible.
- For dashboard changes, perform a manual pass using the checklist in `docs/PLAN-dashboard-streamlit.md`.

## Commit & Pull Request Guidelines
- Commit messages follow `type: summary` (for example, `feat: add dashboard data cache`).
- PRs should include a concise summary, test commands run, and screenshots for UI changes.
- Link related issues or backlog items when available.

## Security, Config, and Workflow Notes
- Store credentials in `.env`; never commit secrets.
- Dashboard pages must consume data via `src/dashboard/data_cache.py`, not direct CSV reads.
- `docs/TASK_BACKLOG.md` is the active workflow board; consult and update it when taking tasks.
## AI Context References
- Documentation index: `.context/docs/README.md`
- Agent playbooks: `.context/agents/README.md`

