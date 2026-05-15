"""
filename: database.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Motor SQLAlchemy y dependencia de sesión FastAPI. Configura NullPool y TCP
             keepalives para Neon free tier. get_db() reintenta 3 veces en cold starts SSL.
"""

import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,       # Sin pool local — Neon usa PgBouncer en su lado
    connect_args={
        "connect_timeout": 10,    # Timeout de conexión TCP
        "keepalives": 1,          # Activar TCP keepalives
        "keepalives_idle": 30,    # Enviar keepalive tras 30s de inactividad
        "keepalives_interval": 5, # Intervalo entre keepalives
        "keepalives_count": 3,    # Intentos antes de cerrar la conexión
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Dependencia FastAPI con reintentos automáticos para cold starts de Neon.

    Neon free tier suspende la BD tras ~5 min de inactividad. El primer request
    post-suspensión falla con `SSL SYSCALL error: EOF detected`. Este generador
    reintenta hasta 3 veces con pausa de 2s para darle tiempo a Neon de
    despertar antes de propagar el error al cliente.

    Uso en routers:
        db: Session = Depends(get_db)
    """
    db = None
    last_error: Exception = RuntimeError("No se pudo conectar a la base de datos.")

    for attempt in range(3):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))  # Fuerza la conexión real antes de entregar la sesión
            break
        except OperationalError as e:
            last_error = e
            if db:
                try:
                    db.close()
                except Exception:
                    pass
                db = None
            if attempt < 2:
                logger.warning(
                    "BD no disponible (intento %d/3), reintentando en 2s: %s",
                    attempt + 1, e
                )
                time.sleep(2)

    if db is None:
        raise last_error

    try:
        yield db
    finally:
        db.close()