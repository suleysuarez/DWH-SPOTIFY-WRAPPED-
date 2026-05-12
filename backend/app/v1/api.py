"""
filename: api.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Agrupa todos los routers de v1 bajo el prefijo /v1.
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
