from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.core.config import settings
import os

config = context.config
selected_url = os.getenv("MIGRATION_DATABASE_URL", settings.database_url)
sync_url = selected_url.replace("+asyncpg", "+psycopg").replace("ssl=require", "sslmode=require")
config.set_main_option("sqlalchemy.url", sync_url.replace("%", "%%"))
if selected_url.startswith("sqlite"):
    raise RuntimeError("Alembic migrations require DATABASE_URL to point to PostgreSQL; SQLite is reserved for the desktop demo")
if config.config_file_name:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
