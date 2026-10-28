# ArcoEnergy architecture

ArcoEnergy is delivered as separate public, mobile and desktop surfaces over one private API and PostgreSQL database:

- `/` and `/seo`: public Next.js marketing site with Spanish metadata, local service areas, FAQ structured data and quote entry points.
- `/app/`: standalone React PWA for sales and field staff. It uses the pinned `gm-pwa` runtime and is built for phone navigation, quote preparation, installations and stock use.
- `/crm/`: separate React application for desktop business operations. It uses the pinned `gm-auth` React client and keeps CRM layout and navigation independent from the PWA.
- `/api/`: FastAPI application with `gm-auth`, role permissions and product endpoints.
- PostgreSQL 16: customers, quote folios, activities, follow-ups, installation tasks, inventory movements, project expenses and receivables.

The Factory hybrid gateway is the only public frontend resource. Its Nginx resolver refreshes private service addresses so Coolify container replacements cannot leave routes pointed at stale container IPs. It routes `/` and `/seo` to Next, `/app` to the PWA, `/crm` to the separate CRM service, and `/api` to FastAPI. All business routes require an authenticated identity with matching permissions. The public package catalog is marked as demonstration data until the customer supplies approved prices and equipment rules.

## Data and integrations

Quotes receive a sequential folio and can be rendered as a PDF download. The generated PDF is labeled as a demo until commercial prices are confirmed. WhatsApp actions create a `wa.me` link so an employee can send a prepared message in the open conversation; the system does not send messages automatically.

Google Drive, electronic contract signatures, identity-document capture, facial checks and electricity-bill analysis remain explicit integration states. Drive credentials and folder policy are required before storing customer contracts or identity documents. The bill-analysis flow is a later phase.

## Authentication

`gm-auth` owns the users, organization memberships, session tokens and permission checks. The first administrator is created only when `ADMIN_BOOTSTRAP_EMAIL` and `ADMIN_BOOTSTRAP_PASSWORD` are injected at runtime. There are no hard-coded demo credentials. Role presets are `admin`, `ventas`, `instalador` and `finanzas`.
