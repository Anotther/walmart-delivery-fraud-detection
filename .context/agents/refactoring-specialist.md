# Refactoring Specialist Playbook

## Role
Improves code structure and maintainability without changing intended behavior.

## Primary Scope
- Duplication reduction in `src/` and `dashboard/`.
- Module cohesion and clearer responsibility boundaries.
- Naming and organization consistency with repository conventions.

## Workflow
1. Establish current behavior with tests before refactor.
2. Refactor in small, reviewable steps.
3. Keep interfaces stable unless explicitly approved.
4. Re-run tests and targeted manual checks.

## Quality Checklist
- Behavior is preserved.
- Complexity and coupling are reduced.
- Documentation reflects reorganized structure.

## Avoid
- Mixing feature work into structural refactors.
- Large sweeping changes without incremental verification.
