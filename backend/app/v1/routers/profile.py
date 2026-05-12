"""
filename: profile.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Rutas de perfil. Endpoint: GET /v1/profile/me.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import DimUsers
from app.v1.schemas.profile import ProfileResponse
from app.v1.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> DimUsers:
    """Valida JWT y retorna usuario actual."""
    try:
        payload = AuthService.verify_jwt_token(credentials.credentials)
        spotify_id: str = payload.get("sub")
        if not spotify_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user = db.query(DimUsers).filter_by(spotify_id=spotify_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    return user


@router.get("/me", response_model=ProfileResponse)
def get_profile(current_user: DimUsers = Depends(get_current_user)):
    """
    Obtiene perfil del usuario autenticado.

    Returns:
        ProfileResponse: Datos del usuario desde dwh.dim_users.
    """
    logger.info(f"Obteniendo perfil para {current_user.spotify_id}")
    return ProfileResponse.from_orm(current_user)
