# TaxSphere India — Software Requirements Specification

## Product objective

TaxSphere India is a multi-tenant SaaS platform for CA firms, businesses, and individual taxpayers. It centralizes bookkeeping, GST, income-tax preparation, TDS/TCS, invoicing, compliance work, documents, notices, and client collaboration.

## Scope and release plan

| Phase | Deliverable |
| --- | --- |
| 1 | Identity, tenant/organization management, configurable RBAC, dashboard, audit foundation |
| 2 | Double-entry accounting, invoicing, customers/vendors, financial statements |
| 3 | GST registrations, effective-dated compliance calendar, return drafts, reconciliation |
| 4 | Taxpayer profiles, income/deductions, versioned tax computation, ITR drafts |
| 5 | TDS/TCS, challans, quarterly return preparation |
| 6 | CA client portal, tasks, document collection, professional billing |
| 7 | Authorized e-invoice/e-way bill integrations, OCR, notices, planning, automations |
| 8 | Security review, observability, resilience, production operations |

## Functional requirements

The system shall isolate every business record by organization; allow configurable roles and membership; record immutable audit events; support organization branches, GST registrations, taxpayers, clients, documents, tasks and filing states. Accounting postings shall balance. Compliance due dates, tax rates, deductions, thresholds and form applicability shall be effective-dated, versioned data rather than application constants.

Returns use `draft`, `validated`, `approved`, `submission_pending`, `submitted`, `acknowledged`, `rejected`, and `failed` states. Only an authorized integration confirmation can set `submitted` or `acknowledged`. Unavailable integrations must provide manual export/import workflows.

## Non-functional requirements

The platform shall provide tenant isolation, least-privilege access, encrypted transport/storage, PII redaction, rate limits, secure uploads, auditability, responsive accessible UI, pagination, structured errors, background jobs, data backups, and observability. Legal and calculation configurations require qualified professional review before production use.

## Out of scope for the foundation

Live government filing, legal-rate assertions, OCR extraction, payment collection, SMS/WhatsApp dispatch, and bank aggregation require separately approved credentials, sandbox testing, contracts, and professional review.

## Commercial MVP priorities

The implementation prioritizes secure multi-client management, automated GST reconciliation, transparent effective-dated tax computations, document intelligence, and a unified compliance dashboard. The first release focuses on preparation, validation and export; it must never represent a filing as submitted without verified authorized-integration acknowledgement.
