"""
filename: artists.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Router de artistas del DWH. Expone GET /v1/artists/top con los top 10 artistas
             del usuario ordenados por reproducciones en fact_listening_history. Requiere JWT.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.models.models import DimUsers, DimArtists, FactListeningHistory
from app.v1.schemas.artists import ArtistsResponse, ArtistResponse
from app.v1.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/artists", tags=["artists"])
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> DimUsers:
    """
    Dependencia compartida: valida JWT Bearer y retorna el usuario DimUsers.
    Lanza HTTP 401 si el token es inválido, expirado o el usuario no existe en BD.
    Nota: esta función se replica en cada router (no hay dependencia centralizada).
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


@router.get("/top", response_model=ArtistsResponse)
def get_top_artists(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene top 10 artistas del usuario ordenados por reproducciones en el DWH.

    Estrategia:
    1. JOIN fact_listening_history → dim_artists, GROUP BY artista, ORDER BY play_count DESC.
    2. Si no hay historial, devuelve artistas de dim_artists ordenados por popularidad.

    Response shape compatible con TopArtistsResponse del frontend (ArtistsResponse).
    """
    logger.info(f"Obteniendo top artistas para {current_user.spotify_id}")

    rows = db.query(
        DimArtists,
        func.count(FactListeningHistory.id).label("play_count")
    ).join(
        FactListeningHistory,
        FactListeningHistory.artist_id == DimArtists.artist_id
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).group_by(
        DimArtists.artist_id
    ).order_by(
        desc("play_count")
    ).limit(10).all()

    artists = []
    for rank, (artist, play_count) in enumerate(rows, start=1):
        artist.play_count = play_count
        artist.rank = rank
        artists.append(ArtistResponse.model_validate(artist))

    return ArtistsResponse(artists=artists, total=len(artists))