# Backend — building geometry case study

FastAPI + uv + async SQLAlchemy. This is a scaffold: it runs and exposes a health
check, has the database plumbing wired, and leaves the geometry domain to you.

## Stack

- **[uv](https://docs.astral.sh/uv/)** — package manager
- **FastAPI** — HTTP API under `/api/v1/`
- **pydantic-settings** — config from env vars (`APP_` prefix)
- **SQLAlchemy (async) + asyncpg** — DB access (engine + session wired, no models)
- **Typer** — CLI (`serve`, `generate-openapi`)
- **Ruff** + **Pyright** — lint/format + type check

## Getting started

```bash
cp .env.example .env
uv sync --group dev
uv run app serve --reload        # http://localhost:8000  (docs at /docs)
```

A Postgres is expected at `APP_DATABASE_URL`. The easiest way is the root
`docker compose up` (brings up db + backend + frontend together).

## What's here / what's yours

- `app/server.py` — FastAPI app, CORS, lifespan; creates the DB engine + session factory.
- `app/db.py` — async engine + `get_session` dependency. **No ORM models** — you design them.
- `app/v1/routes/health.py` — `GET /api/v1/health`.
- `app/geometry/` — empty domain module. **Build the massing algorithm + types here.**

You own: the domain model, the algorithm, the persistence schema (saved options +
the decision tree), migrations, the API contract, and tests.

## Commands

```bash
uv run pytest                              # tests
uv run pytest --cov=app --cov-report=term-missing
uv run ruff check . && uv run ruff format .
uv run pyright
uv run app generate-openapi                # -> docs/openapi.json
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `APP_LOG_LEVEL` | `INFO` | Logging level |
| `APP_DEBUG` | `false` | FastAPI debug mode |
| `APP_ALLOWED_ORIGINS` | `*` | CORS origins, semicolon-separated |
| `APP_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/casestudy` | Async SQLAlchemy URL |
