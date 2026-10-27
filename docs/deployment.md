# Coolify Deployment Contract

This repository is deployed by GoodMorning Factory as independent Coolify resources. A `react` product uses the existing frontend and backend resources; a `next` product uses `/seo` and `/backend`; a `hybrid` product uses private `/frontend` and `/seo` resources plus the public `/gateway` resource. Do not use `compose.yaml` as the remote deployment source; it is local and CI only.

## Hybrid gateway

The gateway is the only public frontend resource for a hybrid product. It listens
on port `80`, proxies `/` and `/seo` to Next, `/app` to React, and `/api` to
the API, and preserves forwarded and WebSocket headers. React is built with
`VITE_BASE_PATH=/app/`; its manifest and service worker are scoped to `/app/`.
Gateway upstreams are injected as internal `SERVICE_URL` bindings by Factory;
the template contains no credentials or environment-specific hostnames.

## Next.js SEO Application

- Source: private repository through the Coolify GitHub App.
- Base directory: `/seo`.
- Dockerfile location: `/Dockerfile` relative to the base directory.
- Build pack: Dockerfile.
- Internal port: `3000`.
- Health path: `/health`.
- Public variables: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_NAME`, and `NEXT_PUBLIC_SITE_DESCRIPTION`.

`NEXT_PUBLIC_*` values are public build-time inputs. They must never contain
credentials, database URLs, API keys, or other secrets.

## Frontend Application

- Source: private repository through the Coolify GitHub App.
- Branch: `dev`.
- Base directory: `/frontend`.
- Dockerfile location: `/Dockerfile` relative to the base directory.
- Build pack: Dockerfile.
- Internal port: `80`.
- Domain: `https://dev.<product>.goodmorning.mx` without a public `:80` suffix.
- Build variable: `VITE_API_URL`.
- Expected dev value: `https://api.dev.<product>.goodmorning.mx`.

`VITE_API_URL` is embedded by Vite during `npm run build`. Changing it requires rebuilding the frontend image. DATABASE_URL must never be added to the frontend runtime or frontend build environment.

## Backend Application

- Source: private repository through the Coolify GitHub App.
- Branch: `dev`.
- Base directory: `/backend`.
- Dockerfile location: `/Dockerfile` relative to the base directory.
- Build pack: Dockerfile.
- Internal port: `8000`.
- Domain: `https://api.dev.<product>.goodmorning.mx` without a public `:8000` suffix.
- Runtime variables:
  - `APP_NAME`.
  - `APP_ENV=dev`.
  - `CORS_ORIGINS=https://dev.<product>.goodmorning.mx`.
  - `DATABASE_URL` as a secret runtime variable.

The backend uses SQLAlchemy with psycopg 3. Therefore `DATABASE_URL` must use the `postgresql+psycopg://` scheme when the backend starts.

Coolify may provide an internal native PostgreSQL URL with the initial scheme `postgresql://`. `goodmorning-factory` is responsible for converting only that initial scheme to `postgresql+psycopg://`. The conversion must not alter the username, password, hostname, port, database, query string, or URL-encoded characters. This template intentionally contains no Coolify integration function and must not know Coolify UUIDs, internal hostnames, or credentials.

## Native PostgreSQL resource

- Resource type: native Coolify PostgreSQL.
- Version: PostgreSQL 16.
- Network exposure: private only.
- Public domain: none.
- Public port: none.
- Credentials: managed by Factory/Coolify outside Git.
- Connectivity: backend reaches PostgreSQL through Coolify's internal network.

## Migration and startup flow

1. The backend receives `DATABASE_URL` from its runtime environment.
2. `/app/entrypoint.sh` runs `python -m app.migrations`.
3. The migration runner obtains a PostgreSQL session advisory lock on one connection, then gives that same connection to Alembic.
4. A second backend release polls for the lock for at most `MIGRATION_LOCK_TIMEOUT_SECONDS` (default: 120 seconds) and fails closed if it cannot acquire it.
5. Alembic upgrades to `head`; the advisory lock is released even when migration execution raises.
6. If locking or migration fails, the shell exits immediately and Uvicorn does not start.
7. After migrations succeed, `exec uvicorn app.main:app --host 0.0.0.0 --port 8000` starts the API process.

Alembic configuration keeps only non-secret migration settings in `backend/alembic.ini`. The dynamic database URL is loaded from backend settings and is not written to `alembic.ini`, printed, or passed through ConfigParser interpolation.

Production revisions must follow expand/contract delivery: deploy additive schema first, deploy compatible application code second, and remove deprecated columns or constraints only in a later release after verification. Before every production backend deployment, Factory verifies a current external backup; a failed migration never triggers an automatic downgrade or destructive schema rollback.

## Local Compose only

`compose.yaml` is documented and configured exclusively for local development and CI:

- The default services are `frontend`, `backend`, and `postgres`. The optional
  `hybrid` profile adds `seo` and `gateway`.
- Frontend builds `./frontend`, receives build args `VITE_API_URL` and
  `VITE_BASE_PATH`, maps local `8080:80`, waits for the backend healthcheck,
  and checks Nginx on port `80`.
- Backend builds `./backend`, maps local `8000:8000`, receives `DATABASE_URL` pointing to `postgres:5432`, waits for PostgreSQL health, and checks `/health` on `127.0.0.1:8000`.
- PostgreSQL uses `postgres:16-alpine`, a persistent `postgres_data` volume, `pg_isready` with the configured user/database, and no host `ports:` mapping.

Do not add Traefik labels, `docker_compose_domains`, Coolify domains, server paths, remote shell/file-copy tooling, or remote deployment settings to `compose.yaml`.

## Environment variable separation

Do not copy every variable from `.env.example` into both Coolify applications. Use only the variables required by each resource:

- Frontend build-time: `VITE_API_URL`, and `VITE_BASE_PATH=/app/` for hybrid.
- Backend runtime: `APP_NAME`, `APP_ENV`, `CORS_ORIGINS`, `DATABASE_URL`.
- Gateway runtime: `REACT_UPSTREAM`, `NEXT_UPSTREAM`, `API_UPSTREAM` as internal
  service URLs. The local hybrid gateway maps to port `8081`.
- Local Compose only: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, plus local placeholder defaults.

No real secrets, credentials, tokens, production identifiers, Coolify UUIDs, or generated hostnames belong in Git.
