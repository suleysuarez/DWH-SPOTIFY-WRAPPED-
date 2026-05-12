"""
filename: history.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Rutas de historial. Endpoint: GET /v1/history/recently-played.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import DimUsers, FactListeningHistory
from app.v1.schemas.history import HistoryResponse, HistoryItemResponse
from app.v1.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/history", tags=["history"])
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


@router.get("/recently-played", response_model=HistoryResponse)
def get_recently_played(
    limit: int = 50,
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene historial de reproducción reciente del usuario.

    Args:
        limit (int): Número de items a retornar (máx 50).

    Returns:
        HistoryResponse: Lista de items del historial.
    """
    logger.info(f"Obteniendo historial reciente para {current_user.spotify_id}")
    
    history = db.query(FactListeningHistory).filter_by(
        user_id=current_user.user_id
    ).order_by(
        FactListeningHistory.played_at.desc()
    ).limit(limit).all()
    
    items = [HistoryItemResponse.from_orm(h) for h in history]
    return HistoryResponse(items=items, total=len(items))
