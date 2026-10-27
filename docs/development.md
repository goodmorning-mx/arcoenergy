# Local development

## Prerequisites

- Docker and Docker Compose
- Node.js 22
- Python 3.12

## Start the hybrid stack

```bash
cp .env.example .env
# Set a local random AUTH_JWT_SECRET before signing in.
docker compose --profile hybrid up --build
```

- Public site and app gateway: <http://localhost:18081>
- PWA: <http://localhost:18081/app/>
- CRM: <http://localhost:18081/crm/>
- API health: <http://localhost:18081/api/health>

No administrator is created without `ADMIN_BOOTSTRAP_EMAIL` and `ADMIN_BOOTSTRAP_PASSWORD`. Local bootstrap credentials should be random and kept outside source control.

## Build checks

```bash
cd frontend && npm ci && npm run typecheck && npm run build
cd crm && npm ci && npm run typecheck && npm run build
cd seo && npm ci && npm run typecheck && npm run build
cd backend && pip install -r requirements.txt && python -m pytest
docker compose --profile hybrid config
```
