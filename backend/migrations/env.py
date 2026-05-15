"""
env.py — Configuración de entorno de Alembic.

Este archivo es ejecutado por Alembic en cada comando (`alembic upgrade`,
`alembic downgrade`, `alembic revision --autogenerate`, etc.).

Responsabilidades:
- Agrega la raíz del backend al sys.path para poder importar `app.*`.
- Inyecta `settings.DATABASE_URL` como la URL de conexión (reemplaza el valor
  en alembic.ini para evitar credenciales en el repositorio).
- Expone `target_metadata = Base.metadata` para la detección automática de
  cambios en los modelos ORM.
- Define `run_migrations_offline()` y `run_migrations_online()` según el
  patrón estándar de Alembic.

Para crear el schema `dwh` antes de las migraciones, la primera migración
(001_initial_schema.py) ejecuta `CREATE SCHEMA IF NOT EXISTS dwh`.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Agregar app al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base

# Alembic Config object
config = context.config

# Configurar sqlalchemy.url desde DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de modelos
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
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
