# ArcoEnergy architecture

ArcoEnergy is delivered as separate public, mobile and desktop surfaces over one private API and PostgreSQL database:

- `/` and `/seo`: public Next.js site with Spanish metadata, local service areas, FAQ structured data, lead capture and a conversational quote assistant.
- `/app/`: standalone React PWA for mobile operations. It uses pinned `gm-pwa` and `gm-auth`, reads the live quote catalog and installation assignments, and keeps mobile navigation independent from the desktop CRM.
- `/crm/`: separate React application for desktop business administration. It uses `gm-auth` for identity and `gm-agent` for a contextual read-only assistant; it manages customers, activity, follow-ups, manual quotes, quote catalog and team access.
- `/api/`: FastAPI application with `gm-auth`, `gm-agent`, `gm-mcp`, role permissions and product endpoints.
- PostgreSQL 16: customers, quote packages and folios, activities, follow-ups, installation tasks, inventory movements, project expenses and receivables.

The Factory hybrid gateway is the only public frontend resource. Its Nginx resolver refreshes private service addresses so Coolify container replacements cannot leave routes pointed at stale container IPs. It routes `/` and `/seo` to Next, `/app` to the PWA, `/crm` to the separate CRM service, and `/api` to FastAPI.

Internal CRM routes require an authenticated identity with matching permissions. Public lead intake requires consent to contact. The public agent can read only enabled system sizes and pricing approval status; it cannot access CRM records or write data. Agent conversations currently live in API process memory and are not durable across restarts.

## Data and integrations

Quotes receive a sequential folio and can be rendered as a PDF download. Seed package values remain marked as demo until an administrator confirms current equipment and prices. The API blocks demo quotes from advancing to commercial states and the frontends block sharing them. For approved quotes, WhatsApp actions create a `wa.me` link so an employee can attach the downloaded PDF in the existing conversation; the system does not send messages automatically.

The PWA inventory view is read-only until consumption can be linked to an installation/project. Google Drive, electronic contract signatures, identity-document capture, facial checks and electricity-bill analysis remain explicit integration states. The privacy page must be completed with the organization's legal identity and rights-request channels before marketing to real prospects.

## GoodMorning modules

Factory DEV pins these module releases by commit:

- `gm-auth@0.1.5`
- `gm-pwa@0.1.5`
- `gm-mcp@0.3.2`
- `gm-billing@0.1.2` (required by `gm-agent`)
- `gm-agent@0.1.6`

The public and CRM agents use `gm-agent` with read-only `gm-mcp` tools. The API gets `OPENAI_API_KEY` through the Factory managed secret binding `goodmorning/openai-default`; no secret is committed here.

## Authentication and roles

`gm-auth` owns users, organization memberships, session tokens and permission checks. The first administrator is created only when `ADMIN_BOOTSTRAP_EMAIL` and `ADMIN_BOOTSTRAP_PASSWORD` are injected at runtime. There are no hard-coded demo credentials. Product role presets are `administrador`, `contador`, `marketing`, `instalador` and `cliente`.
