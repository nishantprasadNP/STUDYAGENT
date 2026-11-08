# StudyPilot AI

A single-user, local **Adaptive Study Management Agent** for DSA (coding interview) preparation.

StudyPilot keeps three records separate:

| Record       | Tables                                                             |
| ------------ | ------------------------------------------------------------------ |
| Planned work | `tasks`                                                            |
| Actual work  | `study_sessions`, `daily_checkins`                                 |
| Next work    | `schedule_revisions` (proposed → validated → approved → applied)   |

**Core rule:** the LLM decides *which* action to take; Python does every calculation,
validation and database write.

## Prerequisites

- Python 3.12 or 3.13 (uv will install it for you; `backend/.python-version` pins 3.13)
- [uv](https://docs.astral.sh/uv/)
- Node.js LTS (>= 22)
- [pnpm](https://pnpm.io/) (version pinned via `packageManager` in `frontend/package.json`)

## Setup

```bash
cp backend/.env.example backend/.env       # optional; defaults work without it
cp frontend/.env.example frontend/.env     # optional
make install                               # raw: cd backend && uv sync ; cd frontend && pnpm install
make migrate                               # raw: cd backend && uv run alembic upgrade head
make seed                                  # raw: cd backend && uv run python -m app.seed
```

## Seed the DSA catalog

`backend/seed/dsa_catalog.json` holds the topic catalog (`{"topics": [...]}`). Load it with:

```bash
make seed
# raw:
cd backend && uv run python -m app.seed                      # default file
cd backend && uv run python -m app.seed --file path.json     # another file
cd backend && uv run python -m app.seed --dry-run            # validate + roll back
```

The seeder is idempotent: it inserts new slugs, updates changed fields, and makes each topic's
prerequisite links match the file exactly. Topics missing from the file are **never deleted**
(later phases reference them); they are listed in a `WARNING` line instead. Any validation error
(bad field, duplicate slug, unknown prerequisite, cycle, empty catalog) writes nothing and exits 1.

## Run

```bash
make dev        # runs both of the following in parallel
make dev-api    # raw: cd backend && uv run uvicorn app.main:app --reload --port 8000
make dev-web    # raw: cd frontend && pnpm dev
```

- API: <http://localhost:8000/api/health>, Swagger UI at <http://localhost:8000/docs>
- Web: <http://localhost:5173> (Vite proxies `/api` → `http://localhost:8000`)

Without `make` (e.g. Windows), run `dev-api` and `dev-web` in two terminals.

## Test

```bash
make test
# raw:
cd backend && uv run pytest --cov=app
cd frontend && pnpm test
```

Backend tests run the real Alembic migration against a fresh SQLite file per test.

## Lint & type-check

```bash
make lint
# raw:
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app
cd frontend && pnpm lint && pnpm typecheck
```

Auto-fix: `cd backend && uv run ruff check --fix . && uv run ruff format .` and `cd frontend && pnpm format`.

## Regenerate API types

With the backend running:

```bash
make gen-api    # raw: cd frontend && pnpm gen:api
```

This writes `frontend/src/api/schema.d.ts` from `/openapi.json`. Commit the result.

## Reset the database

```bash
make reset-db
# raw (macOS/Linux):
rm -f backend/studypilot.db backend/studypilot.db-wal backend/studypilot.db-shm
cd backend && uv run alembic upgrade head
# raw (PowerShell):
Remove-Item backend\studypilot.db* ; cd backend ; uv run alembic upgrade head
```

The schema comes **only** from Alembic migrations. Never call `Base.metadata.create_all()`.
New migration: `cd backend && uv run alembic revision --autogenerate -m "..."`, then review it by hand.

## Roadmap

| Phase | Scope |
| ----- | ----- |
| 0 | Scaffold, environment, schema + migrations, health check, frontend shell, CI ← **done** |
| 1 | Student profile, app settings, DSA topic catalog seed ← **done** |
| 2 | Plan generator: study plans and daily tasks (Today + Plan pages) |
| 3 | Study session logging and progress analytics |
| 4 | Daily check-in flow and APScheduler jobs (check-in prompts, reminders) |
| 5 | Schedule revisions: propose → validate → approve → apply |
| 6 | LLM agent via OpenAI function calling + chat panel |
| 7 | Weekly reports and learning patterns |
| 8 | Charts and dashboard polish (recharts) |
| 9 | Hardening: backups, error handling, packaging |
