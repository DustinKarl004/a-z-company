# Z.A. Company — Backend

FastAPI backend. This slice covers: project skeleton, `branches`/`users` tables, auth (JWT), and admin-only staff/branch management. See the [top-level plan](../README.md) for the full system scope, and the plan file this was built from for what's intentionally left out of this slice (stocks, sales, expenses, monthly rollups, TOTP enrollment, the Vue frontend).

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD
```

## Run migrations

```bash
alembic upgrade head
```

## Seed the default admin

Idempotent — does nothing if an admin already exists.

```bash
python -m app.cli seed-admin
```

## Run the dev server

```bash
uvicorn app.main:app --reload
```

Swagger docs at `http://127.0.0.1:8000/docs`.

## Run tests

```bash
pytest
```

## Notes

- IDs are short random non-sequential strings (12 chars), not autoincrement integers — see `app/core/ids.py`.
- `DATABASE_URL` defaults to local SQLite; point it at a Postgres URL in production.
- `users.totp_secret` exists in the schema but there's no enrollment endpoint yet — login only asks for a TOTP code if that field is already set on the user record.

## Deploying to Railway

1. Create a Railway project, add this repo, and set its **root directory to `backend/`** (it's a monorepo — the frontend lives in `frontend/`).
2. Add a Postgres database in the same Railway project, and set this service's `DATABASE_URL` env var to the Postgres connection string Railway gives you (it may come as `postgres://...` — that's handled automatically, no need to edit it).
3. Set these env vars on the Railway service: `JWT_SECRET` (a real random secret, not the placeholder), `JWT_EXPIRE_MINUTES`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `CORS_ORIGINS` (your Vercel frontend URL, e.g. `https://za-company.vercel.app` — comma-separate multiple origins if needed).
4. Deploy. The `Procfile` runs `alembic upgrade head` automatically before starting the server, so migrations apply on every deploy.
5. After the first deploy, run `python -m app.cli seed-admin` once via Railway's shell/CLI (`railway run python -m app.cli seed-admin`) to create the admin account — it's idempotent, so it's safe to run again by accident.
