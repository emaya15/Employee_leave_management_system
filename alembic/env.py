# alembic/env.py
# This file tells Alembic (1) WHERE the database is and (2) WHAT our tables look like.
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base
import app.models  # noqa: F401  (importing the models registers every table on Base)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 1) Database URL comes from .env (the "%" must be doubled for the ini parser)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

# 2) Base.metadata holds every table defined in app/models.
#    "autogenerate" compares this with the real database to find differences.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without connecting to the database."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and run the migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
