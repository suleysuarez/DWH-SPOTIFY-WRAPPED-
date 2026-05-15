"""
filename: api.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Punto de entrada del API v1. Agrega los routers de auth, profile, artists,
             tracks, history y etl bajo el prefijo /v1.
"""

from fastapi import APIRouter
from app.v1.routers import auth, profile, artists, tracks, history, etl

router = APIRouter(prefix="/v1")

router.include_router(auth.router)
router.include_router(profile.router)
router.include_router(artists.router)
router.include_router(tracks.router)
router.include_router(history.router)
router.include_router(etl.router)
