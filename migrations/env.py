import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# завантаження .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
print(f"Loading .env from: {dotenv_path}")
load_dotenv(dotenv_path)

# DEBUG — перевіримо, чи змінна дійсно підтягується
print("PROJECT_NAME:", os.getenv("PROJECT_NAME"))  # має вивести значення

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from src.config import config_setting
from src.database import Base
import src.models.user_model
import src.models.location_model

# Перевіряємо, що моделі підключені
print("Tables Alembic sees 1:", Base.metadata.tables.keys())

# Alembic Config object
config = context.config

# Замінюємо asyncpg на psycopg2
sync_db_uri = config_setting.DB_URI.replace("postgresql+asyncpg", "postgresql+psycopg2")
config.set_main_option("sqlalchemy.url", sync_db_uri)

print("DB URI used by Alembic:", sync_db_uri)

# Логування
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Вказуємо metadata для Alembic
target_metadata = Base.metadata

print("Tables Alembic sees 2:", Base.metadata.tables.keys())

def run_migrations_offline() -> None:
    context.configure(
        url=sync_db_uri,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()