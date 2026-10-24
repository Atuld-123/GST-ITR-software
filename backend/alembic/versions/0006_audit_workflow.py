"""audit trail and GST filing review state

Revision ID: 0006_audit_workflow
Revises: 0005_reconciliation
"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_audit_workflow"
down_revision = "0005_reconciliation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not context.is_offline_mode():
        bind = op.get_bind()
        existing_roles = bind.execute(sa.text("SELECT id, permissions FROM roles WHERE key = 'organization_admin'")).all()
        roles = sa.table("roles", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("permissions", postgresql.JSONB()))
        for role_id, permissions in existing_roles:
            grants = list(permissions or [])
            grants.extend(p for p in ["gst:*", "accounting:*", "documents:*", "workflow:*", "reconciliation:*", "integrations:*", "audit:read"] if p not in grants)
            bind.execute(roles.update().where(roles.c.id == role_id).values(permissions=grants))
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_table("filing_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gst_registration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gst_registrations.id"), nullable=False),
        sa.Column("period", sa.String(7), nullable=False), sa.Column("status", sa.String(24), nullable=False, server_default="prepared"),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")), sa.Column("review_note", sa.String(1000)),
        sa.Column("acknowledgement_number", sa.String(100)), sa.Column("acknowledgement_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "gst_registration_id", "period", name="uq_filing_review_period"))
    op.create_index("ix_filing_reviews_organization_id", "filing_reviews", ["organization_id"])
    op.create_index("ix_filing_reviews_gst_registration_id", "filing_reviews", ["gst_registration_id"])
    op.create_table("encrypted_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False), sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False), sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_index("ix_encrypted_documents_organization_id", "encrypted_documents", ["organization_id"])
    op.execute("CREATE FUNCTION reject_audit_log_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'audit log entries are append-only'; END; $$")
    op.execute("CREATE TRIGGER audit_logs_no_mutation BEFORE UPDATE OR DELETE ON audit_logs FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mutation()")


def downgrade() -> None:
    op.execute("DROP TRIGGER audit_logs_no_mutation ON audit_logs")
    op.execute("DROP FUNCTION reject_audit_log_mutation()")
    op.drop_table("encrypted_documents")
    op.drop_table("filing_reviews")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
