.PHONY: install migrate seed dev-api dev-web dev lint test gen-api reset-db

install:
	cd backend && uv sync
	cd frontend && pnpm install

migrate:
	cd backend && uv run alembic upgrade head

seed:
	cd backend && uv run python -m app.seed

dev-api:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && pnpm dev

dev:
	$(MAKE) -j2 dev-api dev-web

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app
	cd frontend && pnpm lint && pnpm typecheck

test:
	cd backend && uv run pytest --cov=app
	cd frontend && pnpm test

gen-api:
	cd frontend && pnpm gen:api

reset-db:
	rm -f backend/studypilot.db backend/studypilot.db-wal backend/studypilot.db-shm
	$(MAKE) migrate
