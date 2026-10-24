# TaxSphere India Desktop Edition

## Intended users

This edition is for internal organization administrators and authorized employees only. It does not expose a public client portal. Clients are managed as records by your staff; their documents and communications remain subject to the consent, provider, and access-control workflows that will be implemented in the automation module.

## Desktop operation

The Electron shell is defined in `frontend/desktop/main.cjs`. During development it opens the local web workspace at `http://127.0.0.1:3000`; the local API must be available at `http://127.0.0.1:8000`.

Run `npm run desktop:dev` from `frontend/` after starting the local application services. The packaging task produces an unpacked Windows application at `frontend/release/win-unpacked/`. The executable presently depends on the local TaxSphere API and PostgreSQL services; a bundled backend/service installer is a separate deployment milestone.

## Local-network test

For temporary testing from another desktop on the same trusted LAN, start the frontend with host `0.0.0.0` and use this computer's IPv4 address with port `3000`. The Next.js proxy forwards `/api` requests to the local backend, so other desktop browsers do not use their own `127.0.0.1` for the API. Do not expose this development server to the internet; deploy behind TLS and authenticated network controls for production.

## Access controls

Only administrators and organization members authenticated through `/login` may access protected records. The initial workspace creator is assigned the Organization Admin role. Production rollout must replace development JWT configuration, enable secure secret storage, and enforce full role permissions before use with real client data.
