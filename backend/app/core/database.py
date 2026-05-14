"""
Configuración de la conexión a PostgreSQL con SQLAlchemy.
Incluye pool management para Neon (plan gratuito con límite de conexiones).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Pool ampliado para soportar los ~5 requests simultáneos del dashboard
# Neon free tier permite hasta 10 conexiones concurrentes
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_recycle=300,    # Recicla conexiones cada 5 minutos
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