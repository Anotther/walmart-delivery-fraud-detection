# Documentation Writer Playbook

## Role
Maintains accurate, concise, and task-oriented docs aligned with the actual codebase.

## Primary Scope
- `.context/docs/*`
- `docs/*`
- Architecture, workflow, testing, and security references.

## Workflow
1. Validate behavior in code before documenting.
2. Prefer concrete commands and file references.
3. Keep docs synchronized with changed contracts.
4. Update indexes (`README` docs) when adding/removing pages.

## Quality Checklist
- No TODO placeholders without explicit owner/context.
- Commands are executable as written.
- References and links point to real files.

## Avoid
- Generic text that does not match repository reality.
- Duplicating stale content across multiple docs.
