"""purchase register and gstr2b reconciliation

Revision ID: 0005_reconciliation
Revises: 0004_gst_invoices
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_reconciliation"
down_revision = "0004_gst_invoices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("purchase_invoices", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("gst_registration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gst_registrations.id"), nullable=False), sa.Column("supplier_gstin", sa.String(15), nullable=False), sa.Column("supplier_name", sa.String(300), nullable=False), sa.Column("invoice_number", sa.String(50), nullable=False), sa.Column("invoice_date", sa.Date(), nullable=False), sa.Column("taxable_value", sa.Numeric(18, 2), nullable=False), sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False), sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.UniqueConstraint("gst_registration_id", "supplier_gstin", "invoice_number", name="uq_purchase_invoice"))
    op.create_table("gstr2b_entries", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("gst_registration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gst_registrations.id"), nullable=False), sa.Column("period", sa.String(7), nullable=False), sa.Column("supplier_gstin", sa.String(15), nullable=False), sa.Column("invoice_number", sa.String(50), nullable=False), sa.Column("invoice_date", sa.Date(), nullable=False), sa.Column("taxable_value", sa.Numeric(18, 2), nullable=False), sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.UniqueConstraint("gst_registration_id", "period", "supplier_gstin", "invoice_number", name="uq_gstr2b_entry"))
    op.create_table("reconciliation_runs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("gst_registration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gst_registrations.id"), nullable=False), sa.Column("period", sa.String(7), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="completed"), sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_table("reconciliation_matches", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reconciliation_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("purchase_invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchase_invoices.id", ondelete="CASCADE")), sa.Column("gstr2b_entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gstr2b_entries.id", ondelete="CASCADE")), sa.Column("match_status", sa.String(30), nullable=False), sa.Column("confidence_score", sa.Numeric(5, 2), nullable=False), sa.Column("explanation", sa.String(500), nullable=False))


def downgrade() -> None:
    op.drop_table("reconciliation_matches")
    op.drop_table("reconciliation_runs")
    op.drop_table("gstr2b_entries")
    op.drop_table("purchase_invoices")
