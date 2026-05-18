"""
filename: tracks.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Router de canciones del DWH. Expone GET /v1/tracks/top con los top 10 tracks
             del usuario ordenados por reproducciones en fact_listening_history. Requiere JWT.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.models.models import DimUsers, DimArtists, DimTracks, FactListeningHistory
from app.v1.schemas.tracks import TracksResponse, TrackResponse
from app.v1.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tracks", tags=["tracks"])
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


@router.get("/top", response_model=TracksResponse)
def get_top_tracks(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene top 10 canciones del usuario ordenadas por reproducciones en el DWH.

    Estrategia:
    1. JOIN fact_listening_history → dim_tracks → dim_artists, GROUP BY track, ORDER BY play_count DESC.
    2. Si no hay historial, devuelve canciones de dim_tracks ordenadas por popularidad.

    Args:
        current_user (DimUsers): Usuario autenticado via JWT (inyectado por get_current_user).
        db (Session): Sesión de SQLAlchemy.

    Returns:
        TracksResponse: Lista de hasta 10 canciones con play_count y rank, shape compatible con el frontend.
    """
    logger.info(f"Obteniendo top canciones para {current_user.spotify_id}")

    rows = db.query(
        DimTracks,
        DimArtists.name.label("artist_name"),
        func.count(FactListeningHistory.id).label("play_count")
    ).join(
        FactListeningHistory,
        FactListeningHistory.track_id == DimTracks.track_id
    ).join(
        DimArtists,
        DimArtists.artist_id == DimTracks.artist_id
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).group_by(
        DimTracks.track_id, DimArtists.name
    ).order_by(
        desc("play_count")
    ).limit(10).all()

    tracks = []
    if rows:
        max_plays = max(play_count for _, _, play_count in rows) or 1
        for rank, (track, artist_name, play_count) in enumerate(rows, start=1):
            track.artist_name = artist_name
            track.play_count = play_count
            track.rank = rank
            if track.popularity is None:
                track.popularity = round(play_count * 100 / max_plays)
            tracks.append(TrackResponse.model_validate(track))

    return TracksResponse(tracks=tracks, total=len(tracks))