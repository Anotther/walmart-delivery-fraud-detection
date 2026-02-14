# Security and Compliance Notes

## Secrets and Credentials
- Store DB and service credentials in `.env` only.
- Never commit secrets or local credential variants.
- Use `.env.example` for safe onboarding defaults.

## Data Handling
- Source data contains operational delivery records and should be treated as sensitive business data.
- Do not export raw datasets with personal identifiers to public channels.
- Use aggregated dashboard outputs for reporting whenever possible.

## Access and Runtime Controls
- Restrict PostgreSQL access to authorized local or protected environments.
- Keep least-privilege roles for DB users used by scripts/dashboard.
- Validate environment variables before ETL or dashboard startup.

## Application-level Practices
- Use shared query/data-access layers (`src/database/`, `src/dashboard/data_cache.py`) instead of ad-hoc I/O.
- Avoid dynamic SQL string interpolation; prefer parameterized queries or ORM patterns.
- Treat user-provided filters in dashboard pages as untrusted input.

## Dependency and Platform Hygiene
- Keep Python dependencies updated and monitor known vulnerabilities.
- Re-run tests after dependency upgrades.
- Review Streamlit, Plotly, and SQLAlchemy version changes for security advisories.

## Incident Readiness
- On data corruption or suspicious outputs, stop automated pipelines and inspect ETL logs.
- Track remediation tasks in `docs/TASK_BACKLOG.md`.
- Record root cause and follow-up hardening actions in project docs.

## Related Resources
- `../../AGENTS.md`
- `./testing-strategy.md`
- `../../docs/TASK_BACKLOG.md`
