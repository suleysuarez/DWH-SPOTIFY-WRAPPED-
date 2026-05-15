"""
filename: profile.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Router de perfil de usuario. Expone GET /v1/profile/me que retorna los datos
             del usuario desde dwh.dim_users sin llamar a Spotify en tiempo real. Requiere JWT.
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
    """
    Dependencia FastAPI: valida el JWT Bearer y retorna el registro DimUsers.

    Args:
        credentials (HTTPAuthorizationCredentials): Token Bearer extraído del header Authorization.
        db (Session): Sesión de SQLAlchemy inyectada por get_db.

    Returns:
        DimUsers: Instancia ORM del usuario autenticado.

    Raises:
        HTTPException: 401 si el token es inválido, expirado o el usuario no existe en BD.
    """
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
    Retorna los datos de perfil del usuario autenticado desde el DWH (sin llamar a Spotify en tiempo real).

    Args:
        current_user (DimUsers): Usuario autenticado via JWT (inyectado por get_current_user).

    Returns:
        ProfileResponse: Datos del usuario persistidos en dwh.dim_users
                         (spotify_id, display_name, email, country, followers, product, image_url).
    """
    logger.info(f"Obteniendo perfil para {current_user.spotify_id}")
    return ProfileResponse.model_validate(current_user)
