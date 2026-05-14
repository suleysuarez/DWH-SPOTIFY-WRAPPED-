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
    Obtiene top 10 canciones del usuario ordenadas por reproducciones.
    Retorna shape compatible con TopTracksResponse del frontend.
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
    for rank, (track, artist_name, play_count) in enumerate(rows, start=1):
        track.artist_name = artist_name
        track.play_count = play_count
        track.rank = rank
        tracks.append(TrackResponse.model_validate(track))

    # Si no hay historial, devolver top tracks por popularidad
    if not tracks:
        top = db.query(DimTracks, DimArtists.name.label("artist_name")).join(
            DimArtists, DimArtists.artist_id == DimTracks.artist_id
        ).order_by(desc(DimTracks.popularity)).limit(10).all()

        for rank, (track, artist_name) in enumerate(top, start=1):
            track.artist_name = artist_name
            track.play_count = 0
            track.rank = rank
            tracks.append(TrackResponse.model_validate(track))

    return TracksResponse(tracks=tracks, total=len(tracks))