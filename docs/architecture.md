# ArcoEnergy architecture

ArcoEnergy is delivered as separate public, mobile and desktop surfaces over one private API and PostgreSQL database:

- `/` and `/seo`: public Next.js site with Spanish metadata, local service areas, FAQ structured data, lead capture and a conversational quote assistant.
- `/app/`: standalone React PWA for mobile operations. It uses pinned `gm-pwa` and `gm-auth`, reads the live quote catalog and installation assignments, and supports installation checklists, material consumption/returns, project expenses and camera barcode lookup where the browser supports `BarcodeDetector`. Installers can opt in to server Web Push alerts for new assignments; messages contain only the work-order folio.
- `/crm/`: separate React application for desktop business administration. It uses `gm-auth` for identity and `gm-agent` for a contextual read-only assistant; it manages customers, activity, follow-ups, manual quotes, sales/work orders, inventory/purchases, cash/receivables, operational reports, quote catalog and team access.
- `/api/`: FastAPI application with `gm-auth`, `gm-agent`, `gm-mcp`, role permissions and product endpoints.
- PostgreSQL 16: customers, quote packages and folios, activities, follow-ups, installation tasks, inventory movements, project expenses and receivables.

The Factory hybrid gateway is the only public frontend resource. Its Nginx resolver refreshes private service addresses so Coolify container replacements cannot leave routes pointed at stale container IPs. It routes `/` and `/seo` to Next, `/app` to the PWA, `/crm` to the separate CRM service, and `/api` to FastAPI.

CRM and PWA workspaces require an authenticated identity with matching permissions. `/crm/login` is the desktop sign-in, `/app/login` is the field/customer sign-in and `/login` aliases the CRM sign-in. Customer identities are directed to the PWA client portal. Public lead intake requires consent to contact. The public agent can read enabled system sizes and whether a package is commercially approved; it cannot access CRM records or write data. Agent conversations currently live in API process memory and are not durable across restarts.

ArcoEnergy has no end-user trial mode, trial countdown, demo login or seeded business records. `/` remains the public marketing and lead-capture site; protected routes redirect unauthenticated visitors to their respective login. The word “demo” remains only in test fixtures and migration history about removing old sample rows. Runtime administrator bootstrap credentials are supplied through Factory secrets; real staff and client accounts must be created by an administrator from the organization's actual user list.

## Data and integrations

The product does not load sample customers, quotes, packages, inventory or installations. Quote packages, equipment mapping and prices must be entered and explicitly approved by ArcoEnergy before commercial quotes can be shared or accepted; this is a commercial-data control, not a trial mode. Quotes receive a sequential folio and can be rendered as a PDF download. WhatsApp actions open a prefilled `wa.me` link so an employee can attach the downloaded PDF in the existing conversation; the system does not send messages automatically or store the PDF in Drive.

The PWA can record inventory consumption and returns against assigned work orders, record project expenses, update installation checklists and show local notices while open. It caches previously loaded work orders, inventory and movements per account and queues checklist/material/expense writes while offline for idempotent server synchronization after reconnect. On logout, those cached snapshots are removed; queued unsynchronized writes remain scoped to their owner so work is not lost. CRM follow-up reminders can use Web Push while CRM is closed after a team member opts in; validate delivery on the team's actual browsers/devices. CRM reports show current stock, dated movements, entity statuses and captured expenses. Preliminary profitability adds separately recorded returns and bonifications to sales minus consumed-material cost minus operating expenses, following the accountant's supplied formula. Adjustments are append-only and reversible; they do not themselves change sales, cash or inventory. These reports are not formal financial statements and still require accountant validation. Google Drive, contract templates, identity-document capture, electronic signatures and facial checks require selected providers/credentials and stakeholder approval. Automatic electricity-bill analysis is a later phase. Complete the privacy page with the organization's legal identity and rights-request channels before marketing to real prospects.

## GoodMorning modules

Factory DEV pins these module releases by commit:

- `gm-auth@0.1.5`
- `gm-pwa@0.1.5`
- `gm-mcp@0.3.2`
- `gm-billing@0.1.2` (required by `gm-agent`)
- `gm-agent@0.1.6`

The public and CRM agents use `gm-agent` with read-only `gm-mcp` tools. The API gets `OPENAI_API_KEY` through the Factory managed secret binding `goodmorning/openai-default`; no secret is committed here.

## Authentication and roles

`gm-auth` owns users, organization memberships, session tokens and permission checks. There are no hard-coded or demo credentials. The first administrator is created only when Factory injects `ADMIN_BOOTSTRAP_EMAIL` and `ADMIN_BOOTSTRAP_PASSWORD` at runtime; team administrators create subsequent accounts and assign roles. Product role presets are `administrador`, `contador`, `marketing`, `instalador` and `cliente`.
