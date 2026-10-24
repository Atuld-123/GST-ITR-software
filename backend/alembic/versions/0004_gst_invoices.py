"""gst sales invoices and return drafts

Revision ID: 0004_gst_invoices
Revises: 0003_clients
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_gst_invoices"
down_revision = "0003_clients"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("gst_registrations", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("gstin", sa.String(15), nullable=False), sa.Column("legal_name", sa.String(300), nullable=False), sa.Column("state_code", sa.String(2), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="active"), sa.UniqueConstraint("gstin", name="uq_gstin"))
    op.create_table("sales_invoices", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id")), sa.Column("gst_registration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gst_registrations.id"), nullable=False), sa.Column("invoice_number", sa.String(50), nullable=False), sa.Column("invoice_date", sa.Date(), nullable=False), sa.Column("place_of_supply", sa.String(2), nullable=False), sa.Column("recipient_gstin", sa.String(15)), sa.Column("recipient_name", sa.String(300), nullable=False), sa.Column("taxable_value", sa.Numeric(18, 2), nullable=False), sa.Column("cgst", sa.Numeric(18, 2), nullable=False, server_default="0"), sa.Column("sgst", sa.Numeric(18, 2), nullable=False, server_default="0"), sa.Column("igst", sa.Numeric(18, 2), nullable=False, server_default="0"), sa.Column("cess", sa.Numeric(18, 2), nullable=False, server_default="0"), sa.Column("total_value", sa.Numeric(18, 2), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="draft"), sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.UniqueConstraint("gst_registration_id", "invoice_number", name="uq_sales_invoice_number"), sa.CheckConstraint("status IN ('draft','validated','cancelled')", name="ck_sales_invoice_status"))
    op.create_index("ix_sales_invoices_org_date", "sales_invoices", ["organization_id", "invoice_date"])
    op.create_table("sales_invoice_items", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("sales_invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales_invoices.id", ondelete="CASCADE"), nullable=False), sa.Column("description", sa.String(500), nullable=False), sa.Column("hsn_sac", sa.String(8), nullable=False), sa.Column("quantity", sa.Numeric(18, 3), nullable=False), sa.Column("taxable_value", sa.Numeric(18, 2), nullable=False), sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False), sa.CheckConstraint("quantity > 0 AND taxable_value >= 0 AND gst_rate >= 0", name="ck_sales_item_values"))


def downgrade() -> None:
    op.drop_table("sales_invoice_items")
    op.drop_table("sales_invoices")
    op.drop_table("gst_registrations")
