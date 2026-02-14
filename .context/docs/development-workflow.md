# Development Workflow

## Branch and Task Management
- Use `docs/TASK_BACKLOG.md` as the active board before starting work.
- Keep tasks tagged by ownership (`[BACKEND]`, `[FRONTEND]`, `[GERAL]`).
- Move work across sections (`A Fazer` -> `Em Progresso` -> `Concluido`) rather than deleting history.

## Local Setup
1. `pip install -r requirements.txt`
2. Configure `.env` from `.env.example`
3. Initialize DB: `python scripts/setup_database.py`
4. Validate app startup: `streamlit run dashboard/app.py`

## Standard Delivery Flow
1. Read impacted modules and existing docs.
2. Implement code changes in smallest coherent scope.
3. Run relevant tests (`pytest tests/` and targeted scripts).
4. For dashboard changes, execute manual checklist from `docs/PLAN-dashboard-streamlit.md`.
5. Update docs/backlog when behavior changes.

## Coding Rules
- Python style: PEP 8, type hints where practical.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes.
- Dashboard pages: numeric filename prefix (for example `1_Overview.py`).
- SQL migrations: ordered prefix in `src/database/sql/`.
- Dashboard visuals must use theme tokens from `src/config/viz_theme.py`.

## Data and Contract Rules
- Preserve known source quirks (for example `products_data.csv` uses `produc_id`).
- Dashboard pages must consume data via `src/dashboard/data_cache.py`.
- Avoid direct CSV access from UI layer.

## Commit and PR Expectations
- Commit message format: `type: summary` (for example `feat: add dashboard data cache`).
- Include test commands executed in PR description.
- Include screenshots for UI-impacting changes.

## Related Resources
- `../../AGENTS.md`
- `../../docs/TASK_BACKLOG.md`
- `./testing-strategy.md`
