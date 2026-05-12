"""
Aplicación FastAPI principal.
Configuración de CORS, routers, logging.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.routers import auth, data, etl

# Configurar logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Crear tablas (en desarrollo; en producción usar Alembic)
Base.metadata.create_all(bind=engine)

# Crear aplicación
app = FastAPI(
    title="Mi Spotify Wrapped DWH",
    description="Backend FastAPI para Personal Data Warehouse de Spotify",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(etl.router)


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
