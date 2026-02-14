# Performance Optimizer Playbook

## Role
Improves runtime and interaction performance across ETL, analytics, models, and dashboard loading.

## Primary Scope
- `src/dashboard/data_cache.py` cache paths.
- Heavy dataframe transforms in `src/features/` and `src/analysis/`.
- Query and load efficiency in `src/database/` and `src/etl/`.

## Workflow
1. Identify bottlenecks with reproducible timing context.
2. Prioritize high-impact optimizations with low behavioral risk.
3. Preserve output equivalence while reducing cost.
4. Validate performance and correctness post-change.

## Quality Checklist
- Optimizations are measurable and documented.
- No silent correctness trade-offs.
- Cache invalidation behavior remains explicit.

## Avoid
- Premature micro-optimizations without evidence.
- Memory-heavy shortcuts that hurt dashboard stability.
