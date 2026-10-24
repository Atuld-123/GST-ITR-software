"""associate encrypted documents with clients

Revision ID: 0007_client_document_links
Revises: 0006_audit_workflow
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_client_document_links"
down_revision = "0006_audit_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("encrypted_documents", sa.Column("client_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_encrypted_documents_client_id_clients", "encrypted_documents", "clients", ["client_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_encrypted_documents_client_id", "encrypted_documents", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_encrypted_documents_client_id", table_name="encrypted_documents")
    op.drop_constraint("fk_encrypted_documents_client_id_clients", "encrypted_documents", type_="foreignkey")
    op.drop_column("encrypted_documents", "client_id")
