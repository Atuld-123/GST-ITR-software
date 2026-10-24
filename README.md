# TaxSphere India

Multi-tenant Indian tax, GST, accounting and CA-firm compliance platform.

## Current scope

Current foundation: tenant-aware API, PostgreSQL Alembic migrations, organization roles, encrypted document storage, GST invoice calculation/export and internal review workflow, plus a limited AY 2026-27 salary tax estimate prepared for CA review. Full ITR computation and live government filing remain gated on complete reviewed rules and authorized credentials.

## Local development

1. Copy `backend/.env.example` to `backend/.env` and configure `DATABASE_URL`.
2. Start infrastructure with `docker compose up -d db redis`.
3. Backend: `cd backend; pip install -e .; uvicorn app.main:app --reload`. PostgreSQL is exposed locally on port `5433` to avoid conflicts with existing local database services.
4. Frontend: `cd frontend; npm install; npm run dev`.

PostgreSQL schema upgrades: `cd backend; alembic upgrade head`. For production requirements and HTTPS/backup setup, see `docs/DEPLOYMENT.md`.

Production stack: copy `.env.production.example` to a protected `.env.production`, replace every placeholder, provide both TLS certificates, then follow `docs/DEPLOYMENT.md`.

## Windows desktop application

TaxSphere is designed for internal administrator and employee use; there is no public client portal in this edition. After installing frontend dependencies, run `npm run desktop:dev` while the local web service is running. The Windows application is packaged under `frontend/release/win-unpacked/`. The desktop shell requires the local TaxSphere web and API services to be running until the bundled service mode is added. See `docs/DESKTOP_DEPLOYMENT.md`.

See `docs/` for the SRS, architecture, API contract, data model, security posture, testing plan, and deployment plan.
