# Database Specialist Playbook

## Role
Maintains PostgreSQL schema, views, and query performance for analytics and dashboard consumption.

## Primary Scope
- `src/database/sql/*.sql`
- `src/database/models.py`
- `src/database/manager.py`
- ETL load behavior in `src/etl/loaders.py`

## Workflow
1. Review schema/view impact of requested change.
2. Keep SQL migration ordering and naming conventions.
3. Validate compatibility with ETL loaders and model inputs.
4. Test setup path: `python scripts/setup_database.py`.

## Quality Checklist
- Schema changes are backward-compatible or clearly documented.
- Views used by analytics/dashboard remain valid.
- Index/constraint choices reflect query and integrity needs.

## Avoid
- Untracked schema drift outside `src/database/sql/`.
- Breaking setup scripts by changing table contracts silently.
