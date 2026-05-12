"""
filename: tracks.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Rutas de canciones. Endpoint: GET /v1/tracks/top.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.models.models import DimUsers, DimTracks, FactListeningHistory
from app.v1.schemas.tracks import TracksResponse, TrackResponse
from app.v1.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tracks", tags=["tracks"])
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


@router.get("/top", response_model=TracksResponse)
def get_top_tracks(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene top 5 canciones del usuario.

    Basado en conteo de reproducciones en dwh.fact_listening_history.

    Returns:
        TracksResponse: Lista de top canciones.
    """
    logger.info(f"Obteniendo top canciones para {current_user.spotify_id}")
    
    top_tracks = db.query(
        DimTracks,
        func.count(FactListeningHistory.id).label("play_count")
    ).join(
        FactListeningHistory,
        FactListeningHistory.track_id == DimTracks.track_id
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).group_by(
        DimTracks.track_id
    ).order_by(
        desc("play_count")
    ).limit(5).all()
    
    tracks = [TrackResponse.from_orm(track[0]) for track in top_tracks]
    return TracksResponse(items=tracks)
