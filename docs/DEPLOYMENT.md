# Deployment

## Production rollout

1. Copy `.env.production.example` to a protected `.env.production`; replace every placeholder with unique secrets. URL-encode database passwords. Never commit the populated file.
2. Create a public TLS certificate for the service domain and a separate PostgreSQL TLS certificate whose SAN includes `db`. Place the public `fullchain.pem` and `privkey.pem` under `EDGE_TLS_DIRECTORY` and configure the PostgreSQL certificate paths.
3. Point DNS to the host and open inbound ports 80 and 443 only. Keep PostgreSQL and Redis on the private Compose network.
4. Run `docker compose --env-file .env.production -f docker-compose.production.yml up -d --build`. Compose builds non-root API/web containers, creates separate PostgreSQL bootstrap/runtime/migrator roles on a fresh volume, runs Alembic migrations, and starts the Nginx HTTPS edge.
5. If PostgreSQL already has a data volume, create the app and migration roles manually before deployment. The bootstrap init script runs only when PostgreSQL initializes a fresh data directory.
6. Verify `/health`, sign-in, organization membership, document upload/download, GST estimate/export and review permissions using test data. Do not use real filings until the tax workflow and security review are approved.

## Render preview

The root `render.yaml` defines a preview deployment with a Docker API, a Docker web service and PostgreSQL. In Render, choose **New > Blueprint**, connect the GitHub repository, and apply the Blueprint. Render will ask for `DOCUMENTS_ENCRYPTION_KEY`; generate it with the command below and save it as a Render secret. The Blueprint runs database migrations when the API starts and routes browser API calls through the public HTTPS API hostname.

This free configuration is for a temporary preview only. Render's free PostgreSQL database expires after 30 days and has no backups; free web services can sleep when idle. Do not store real client documents or production records there. For production, change both web plans and the database to paid plans, set up backups and restore checks, and review database role separation and operational monitoring before onboarding clients. The single Render database uses one owner connection for API and migrations, so it does not yet provide the separate runtime and migrator roles used by the Docker Compose production setup.

Render Blueprint deployment requires the GitHub repository to be connected to the Render account. The repo itself does not contain the secret key.

Generate secrets without putting them in source control: `python -c "import secrets; print(secrets.token_urlsafe(48))"` for `JWT_SECRET` and database passwords; `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` for `DOCUMENTS_ENCRYPTION_KEY`. Use independent values for each secret.

## Configuration and security

- The API refuses production startup unless `APP_ENVIRONMENT=production`, `DATABASE_URL` is PostgreSQL with `ssl=require`, `JWT_SECRET` is a non-placeholder secret of at least 32 characters, the frontend origin uses HTTPS, and `DOCUMENTS_ENCRYPTION_KEY` is a valid Fernet key.
- Keep bootstrap, app runtime and migrator database credentials separate. Runtime DB role has data access; migrator role owns schema objects. The app role cannot create tables.
- PostgreSQL TLS is enabled. Nginx redirects HTTP to HTTPS, accepts TLS 1.2/1.3, and applies basic per-IP request limits. Renew public and database certificates before expiry.
- Roles are organization-scoped: administrator, tax preparer, reviewer and read-only. Filing creator and approver must be different users. Acknowledgements remain marked unverified until authorized portal integration is available.
- PDF/JPEG/PNG files (up to 10 MB) are Fernet-encrypted before database storage and their type is checked against file signatures. Generate the key once, store it in a secret manager, and keep a protected recovery copy. Losing the key makes stored documents unrecoverable. Key rotation and malware scanning are not automated yet.
- Use `backend/scripts/backup-postgres.ps1` with protected `PGSERVICEFILE` and `PGPASSFILE` configurations. Schedule backups and copy them to encrypted off-site storage. Configure point-in-time recovery where supported and run documented restore drills before launch.

## Remaining provider operations

This repository contains the application containers, migration step and HTTPS edge configuration. The hosting account, DNS, certificate issuance/renewal, secret manager, monitoring/alerting, off-site backup target, restore drill, independent security review and incident response contacts must be configured with the selected provider/team. Do not store production client records before those controls are active.
