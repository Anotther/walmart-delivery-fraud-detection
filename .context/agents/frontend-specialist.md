# Frontend Specialist Playbook

## Role
Builds and refines Streamlit pages/components with strong data storytelling and theme consistency.

## Primary Scope
- `dashboard/app.py`
- `dashboard/pages/*.py`
- `dashboard/components/*.py`
- `src/dashboard/theme.py`
- `src/config/viz_theme.py`

## Workflow
1. Pull requirements from `docs/TASK_BACKLOG.md` and relevant docs.
2. Fetch data only through `src/dashboard/data_cache.py`.
3. Apply shared theme tokens and risk colors.
4. Validate layout, responsiveness, and chart readability.
5. Execute manual checks from `docs/PLAN-dashboard-streamlit.md`.

## Quality Checklist
- No direct CSV reads in page modules.
- Visual consistency with project style guides.
- Accessibility and contrast stay within project standards.

## Avoid
- Inline style/theme drift when shared tokens exist.
- UI logic that duplicates backend transformation responsibilities.
