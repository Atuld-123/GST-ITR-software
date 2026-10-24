"""client management foundation

Revision ID: 0003_clients
Revises: 0002_accounting
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_clients"
down_revision = "0002_accounting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("client_type", sa.String(30), nullable=False),
        sa.Column("pan", sa.String(10)),
        sa.Column("email", sa.String(320)),
        sa.Column("mobile", sa.String(20)),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("client_type IN ('individual','proprietorship','partnership','llp','company','trust','other')", name="ck_client_type"),
        sa.CheckConstraint("status IN ('active','inactive','archived')", name="ck_client_status"),
        sa.UniqueConstraint("organization_id", "pan", name="uq_client_pan_per_org"),
    )
    op.create_index("ix_clients_org_status", "clients", ["organization_id", "status"])
    op.create_table(
        "client_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organization_members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("client_id", "member_id", name="uq_client_assignment"),
    )
    op.create_index("ix_client_assignments_org_member", "client_assignments", ["organization_id", "member_id"])


def downgrade() -> None:
    op.drop_table("client_assignments")
    op.drop_table("clients")
