from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

engine_options = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
database_url = settings.database_url
engine = create_async_engine(database_url, **engine_options)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def initialize_database() -> None:
    # SQLite create_all is retained for the local desktop demo. PostgreSQL schema
    # changes must be applied by the versioned Alembic release migration.
    if settings.database_url.startswith("sqlite"):
        from app.models import Base
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            def ensure_client_document_link(sync_connection):
                columns = sync_connection.exec_driver_sql("PRAGMA table_info(encrypted_documents)").fetchall()
                if columns and not any(column[1] == "client_id" for column in columns):
                    sync_connection.exec_driver_sql("ALTER TABLE encrypted_documents ADD COLUMN client_id CHAR(32) REFERENCES clients(id) ON DELETE SET NULL")
                if columns and not any(column[1] == "service_case_id" for column in columns):
                    sync_connection.exec_driver_sql("ALTER TABLE encrypted_documents ADD COLUMN service_case_id CHAR(32)")
                if columns and not any(column[1] == "document_label" for column in columns):
                    sync_connection.exec_driver_sql("ALTER TABLE encrypted_documents ADD COLUMN document_label VARCHAR(200)")
                sync_connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_encrypted_documents_client_id ON encrypted_documents (client_id)")
                sync_connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_encrypted_documents_service_case_id ON encrypted_documents (service_case_id)")
            await connection.run_sync(ensure_client_document_link)
