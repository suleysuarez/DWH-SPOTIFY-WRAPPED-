"""
Configuración de la conexión a PostgreSQL con SQLAlchemy.
Incluye pool management para Neon (plan gratuito con límite de conexiones).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Engine con pool_size reducido para Neon (plan gratuito)
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=2,
    max_overflow=3,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency para inyectar sesión de BD en endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
