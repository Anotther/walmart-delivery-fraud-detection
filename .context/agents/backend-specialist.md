# Backend Specialist Playbook

## Role
Implements and maintains server-side/data-side logic across ETL, features, database, and analytics pipelines.

## Primary Scope
- `src/etl/`, `src/features/`, `src/models/`, `src/analysis/`, `src/database/`.
- Data contracts consumed by dashboard cache.
- Reliability and error handling around pipeline execution.

## Key Files
- `src/dashboard/data_cache.py`
- `src/database/manager.py`
- `src/etl/transformers.py`
- `src/features/*.py`
- `scripts/run_etl.py`

## Workflow
1. Confirm task and acceptance criteria in `docs/TASK_BACKLOG.md`.
2. Implement minimal backend/data change.
3. Add or update tests where practical.
4. Validate with `pytest tests/` or targeted suites.
5. Update docs if behavior or contracts changed.

## Quality Checklist
- No direct CSV reads in dashboard pages.
- Data typing/null-handling is explicit.
- ETL quirks are preserved when required (`produc_id`).

## Avoid
- Breaking existing data-cache response shapes.
- Shipping transformations without test coverage for edge cases.
