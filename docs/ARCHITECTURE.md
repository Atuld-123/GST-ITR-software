# Architecture

TaxSphere begins as a modular monolith with a Next.js/TypeScript web client and FastAPI/Python API. PostgreSQL is the transactional source of truth; Redis backs jobs and cache; S3-compatible object storage contains encrypted documents. A worker process handles imports, OCR, notifications, reconciliation, and integration retries.

```text
Browser -> Next.js -> FastAPI -> PostgreSQL
                       |-> Redis / workers
                       |-> Object storage
                       |-> Authorized GSP, GSTN, Income Tax, payment and messaging adapters
```

Domain boundaries: identity, organizations/RBAC, clients, accounting, invoicing, GST, reconciliation, income-tax, TDS/TCS, documents, notices, workflow, notifications, integrations, and audit. Each adapter redacts secrets and raw sensitive fields from logs. Events use an outbox table before asynchronous dispatch.

## Security architecture

JWT bearer access tokens are short-lived (15 minutes). Passwords use Argon2. All business requests are tenant-scoped from authenticated membership, never a caller-provided tenant id. RBAC checks are enforced in route dependencies. The initial implementation does not yet provide refresh-token rotation. Production also requires TLS, managed encryption-key storage, malware scanning for uploads, CSP/CSRF review, rate limiting, backups, and external security review.

## Wireframe

```text
+Sidebar---------+ +Top: Search | Organization | FY | Alerts | Profile+
| Dashboard       | +-----------------------------------------------+
| My Clients      | | KPI cards: sales | ITC | tax due | tasks         |
| GST             | | compliance health | trends | due dates          |
| Income Tax      | +-----------------------------------------------+
| TDS / TCS       | | actionable queues and filtered work tables     |
| Accounting      | +-----------------------------------------------+
| ...             |
+-----------------+
```
