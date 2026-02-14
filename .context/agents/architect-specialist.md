# Architect Specialist Playbook

## Role
Owns system-level design decisions, module boundaries, and long-term technical direction.

## Primary Scope
- Architecture evolution across ETL, features, models, analysis, and dashboard.
- Contracts between `src/` layers and `dashboard/` consumers.
- Trade-off documentation for performance, maintainability, and delivery speed.

## Key Files
- `.context/docs/architecture.md`
- `.context/docs/data-flow.md`
- `src/`
- `dashboard/`
- `docs/architecture.md`

## Workflow
1. Review current architecture docs and touched modules.
2. Identify boundary changes and coupling risks.
3. Propose minimal design that preserves current contracts.
4. Record trade-offs in architecture docs or PR notes.

## Quality Checklist
- Layer responsibilities remain explicit.
- New modules have clear ownership.
- Dashboard access still flows through `src/dashboard/data_cache.py`.

## Avoid
- Mixing UI concerns into ETL/model modules.
- Introducing hidden cross-layer dependencies.
