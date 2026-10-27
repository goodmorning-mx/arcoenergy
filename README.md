# ArcoEnergy

Solar sales and field operations for the ArcoEnergy team. The DEV product has three independent experiences on the GoodMorning Factory hybrid profile:

- Public SEO/GEO website: `/` — service information for Tampico, Ciudad Madero and Altamira.
- Mobile field and sales PWA: `/app/` — separate React app using `gm-pwa` and `gm-auth`.
- Desktop CRM: `/crm/` — separate React app using `gm-auth`.
- Shared FastAPI service: `/api/` — PostgreSQL, authentication, role permissions and ArcoEnergy domain endpoints.

The database supports customer records, sequential quote folios and PDF downloads, activity notes and follow-ups, installation assignments, inventory movements, project expenses and receivables. Static sample screens are clearly labeled as demonstration data; pricing and equipment mappings in the API catalog are provisional.

## Integrations with pending configuration

PDFs can be generated and downloaded. Google Drive requires the customer's folder policy and credentials before documents are stored externally. WhatsApp opens a prefilled `wa.me` link for an employee to send. Contract templates, ID document handling, electronic signatures and facial verification need a selected provider and legal/security review. Automatic electricity bill analysis is a later phase.

## Local development

```bash
cp .env.example .env
# Set a random AUTH_JWT_SECRET; set admin bootstrap values only in local .env.
docker compose --profile hybrid up --build
```

- Site: <http://localhost:18081>
- PWA: <http://localhost:18081/app/>
- CRM: <http://localhost:18081/crm/>
- API: <http://localhost:18081/api/health>

Compose is for local development. DEV/PROD are separately managed Factory and Coolify resources. The product manifest in the Factory repository owns the hybrid routes, app resources, module pins and generated runtime bindings.

## Verify changes

```bash
cd frontend && npm ci && npm run typecheck && npm run build
cd crm && npm ci && npm run typecheck && npm run build
cd seo && npm ci && npm run typecheck && npm run build
cd backend && pip install -r requirements.txt && python -m pytest
docker compose --profile hybrid config
```

Read [architecture](docs/architecture.md), [development](docs/development.md), [deployment](docs/deployment.md) and [rollback](docs/rollback.md) for more detail. Changes target `dev` through reviewable feature branches; `main` remains production.
