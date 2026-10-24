# API Contract — Foundation

All responses use JSON. Authentication is bearer JWT; tenant access is derived from the authenticated membership.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | service health |
| POST | `/api/v1/auth/register` | create user and initial organization |
| POST | `/api/v1/auth/login` | create a secure session |
| GET | `/api/v1/organizations` | list organizations the user belongs to |
| POST | `/api/v1/organizations` | create organization |
| GET | `/api/v1/organizations/{id}/members` | list members (permission protected) |
| POST | `/api/v1/organizations/{id}/members` | invite/add member (permission protected) |
| POST | `/api/v1/accounting/organizations/{id}/accounts` | create chart-of-account entry |
| POST | `/api/v1/accounting/journal-entries` | post validated balanced journal entry |
| GET | `/api/v1/organizations/{id}/clients` | list active tenant-isolated clients |
| GET | `/api/v1/organizations/{id}/clients/{client_id}` | open an organization-scoped client profile |
| POST | `/api/v1/organizations/{id}/clients` | create client with PAN uniqueness protection |
| POST | `/api/v1/organizations/{id}/gst/registrations` | add an active GST registration |
| GET | `/api/v1/organizations/{id}/gst/registrations` | list active GST registrations for a tenant |
| POST | `/api/v1/organizations/{id}/gst/sales-invoices` | validate a sales invoice and calculate CGST/SGST or IGST |
| GET | `/api/v1/organizations/{id}/gst/gstr-1-summary` | prepare monthly GSTR-1 sales summary; never submits a filing |
| GET | `/api/v1/organizations/{id}/gst/gstr-1-export` | download prepared invoice rows as JSON or CSV |
| POST/GET | `/api/v1/organizations/{id}/gst/filing-reviews` | create and list internal return review items |
| POST | `/api/v1/organizations/{id}/gst/filing-reviews/{review_id}/decision` | approve internally or request changes |
| POST | `/api/v1/organizations/{id}/gst/filing-reviews/{review_id}/acknowledgement` | record an ARN as unverified pending authorized portal check |
| POST/GET | `/api/v1/organizations/{id}/documents` | upload/list encrypted PDF, JPEG or PNG files; upload accepts optional `client_id`, `service_case_id`, and `document_label` fields |
| GET | `/api/v1/organizations/{id}/documents?client_id={client_id}` | list encrypted files linked to one client |
| GET | `/api/v1/organizations/{id}/documents?unassigned=true` | list workspace files that can be reviewed and linked to a client |
| POST | `/api/v1/organizations/{id}/documents/{document_id}/link` | link an unassigned encrypted file to an organization client |
| GET | `/api/v1/organizations/{id}/documents/{document_id}/download` | decrypt and download a tenant-scoped file |
| GET | `/api/v1/organizations/{id}/audit-log` | list tenant audit events (audit permission required) |
| POST | `/api/v1/income-tax/estimate` | calculate a limited AY 2026-27 old/new regime salary estimate for CA review |
| POST | `/api/v1/organizations/{id}/reconciliation/purchase-invoices` | record purchase-register invoice |
| POST | `/api/v1/organizations/{id}/reconciliation/gstr2b-entries` | import a normalized GSTR-2B invoice row |
| POST | `/api/v1/organizations/{id}/reconciliation/runs` | create explainable GST purchase-vs-2B match results |

Future API groups are versioned under `/api/v1/{accounting,gst,income-tax,tds,documents,workflow,reconciliation,reports}`. API requests for filings expose preparation and validation only unless an integration acknowledgement is persisted.
