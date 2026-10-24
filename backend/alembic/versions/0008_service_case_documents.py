"""attach encrypted files to local service case references

Revision ID: 0008_service_case_documents
Revises: 0007_client_document_links
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_service_case_documents"
down_revision = "0007_client_document_links"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("encrypted_documents", sa.Column("service_case_id", sa.Uuid(), nullable=True))
    op.add_column("encrypted_documents", sa.Column("document_label", sa.String(200), nullable=True))
    op.create_index("ix_encrypted_documents_service_case_id", "encrypted_documents", ["service_case_id"])


def downgrade() -> None:
    op.drop_index("ix_encrypted_documents_service_case_id", table_name="encrypted_documents")
    op.drop_column("encrypted_documents", "document_label")
    op.drop_column("encrypted_documents", "service_case_id")
