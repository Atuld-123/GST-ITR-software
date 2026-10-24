# Data Model

```text
users --< organization_members >-- organizations --< branches
organizations --< clients --< taxpayer_profiles
organizations --< gst_registrations --< gst_returns --< gst_return_items
organizations --< invoices --< invoice_items
organizations --< journal_entries --< journal_entry_lines >-- chart_of_accounts
organizations --< documents, notices, compliance_tasks, audit_logs
clients --< encrypted_documents (optional client link)
tax_rule_versions --< tax_rules / tax_computations
```

Every tenant-owned table includes `organization_id`, creation/update timestamps, and relevant actor metadata. Unique constraints prevent duplicate membership and accounting lines use check constraints so debit and credit cannot both be populated. A deferred database trigger will enforce journal balance when accounting is implemented.

See `backend/alembic/versions/0001_foundation.py` for the executable foundation schema.
