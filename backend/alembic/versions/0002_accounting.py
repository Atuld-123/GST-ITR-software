"""accounting foundation

Revision ID: 0002_accounting
Revises: 0001_foundation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_accounting"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("chart_of_accounts", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("code", sa.String(32), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("account_type", sa.String(20), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.UniqueConstraint("organization_id", "code", name="uq_account_code"), sa.CheckConstraint("account_type IN ('asset','liability','equity','income','expense')", name="ck_account_type"))
    op.create_table("journal_entries", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("entry_date", sa.Date(), nullable=False), sa.Column("reference", sa.String(100)), sa.Column("narration", sa.String(500), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="posted"), sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.CheckConstraint("status IN ('draft','posted','void')", name="ck_journal_status"))
    op.create_index("ix_journal_entries_org_date", "journal_entries", ["organization_id", "entry_date"])
    op.create_table("journal_entry_lines", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False), sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chart_of_accounts.id"), nullable=False), sa.Column("debit", sa.Numeric(18, 2), nullable=False, server_default="0"), sa.Column("credit", sa.Numeric(18, 2), nullable=False, server_default="0"), sa.Column("description", sa.String(500)), sa.CheckConstraint("(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)", name="ck_journal_line_single_side"))


def downgrade() -> None:
    op.drop_table("journal_entry_lines")
    op.drop_table("journal_entries")
    op.drop_table("chart_of_accounts")
