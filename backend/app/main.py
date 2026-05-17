"""
filename: main.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Punto de entrada de la aplicación FastAPI. Configura logging, CORS y tablas
             del DWH en startup, y monta el router v1 con todos los endpoints bajo /v1.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.v1.api import router as v1_router

# Configurar logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Crear tablas (en desarrollo; en producción usar Alembic)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"No se pudo crear tablas al iniciar: {e}")

# Crear aplicación
app = FastAPI(
    title="Mi Spotify Wrapped DWH",
    description="Backend FastAPI para Personal Data Warehouse de Spotify",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allow_hosts(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(v1_router)


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "service": "Mi Spotify Wrapped DWH Backend"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

