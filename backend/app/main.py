"""
filename: main.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Punto de entrada de la aplicación FastAPI. Configura logging, CORS,
             middlewares de rate limiting y logging de requests, y monta el router
             v1 con todos los endpoints bajo /v1.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
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

# ── Middlewares ────────────────────────────────────────────────────────────────
# Orden importa: el primero en agregarse es el más externo (último en ejecutarse).

# 1. CORS — debe ir primero para que las preflight OPTIONS pasen sin rate limit
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allow_hosts(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate limiting — 100 requests/minuto por IP
app.add_middleware(
    RateLimitMiddleware,
    max_requests=100,
    window_seconds=60,
)

# 3. Request logging — loguea método, path, status y duración
app.add_middleware(RequestLoggingMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(v1_router)


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "service": "Mi Spotify Wrapped DWH Backend"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/circuit-breakers")
def circuit_breaker_status():
    """
    Retorna el estado actual de los circuit breakers.
    Útil para monitorear la salud de los servicios externos.
    """
    from app.core.circuit_breaker import lastfm_breaker, spotify_breaker
    return {
        "circuit_breakers": [
            lastfm_breaker.get_status(),
            spotify_breaker.get_status(),
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)