"""
filename: history.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Rutas de historial. Endpoints: recently-played, stats, genres, peak-hour.
"""
import logging
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.models.models import DimUsers, DimArtists, FactListeningHistory
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
    """Obtiene historial de reproducción reciente del usuario."""
    logger.info(f"Obteniendo historial reciente para {current_user.spotify_id}")
    history = db.query(FactListeningHistory).filter_by(
        user_id=current_user.user_id
    ).order_by(
        FactListeningHistory.played_at.desc()
    ).limit(limit).all()
    items = [HistoryItemResponse.from_orm(h) for h in history]
    return HistoryResponse(items=items, total=len(items))


@router.get("/stats")
def get_history_stats(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Estadísticas rápidas del DWH.
    Shape: { total_tracks, total_artists, last_sync, etl_status }
    Compatible con QuickStats del frontend.
    """
    logger.info(f"Obteniendo stats para {current_user.spotify_id}")

    total_tracks = db.query(func.count(func.distinct(FactListeningHistory.track_id))).filter_by(
        user_id=current_user.user_id
    ).scalar() or 0

    total_artists = db.query(func.count(func.distinct(FactListeningHistory.artist_id))).filter_by(
        user_id=current_user.user_id
    ).scalar() or 0

    last_play = db.query(func.max(FactListeningHistory.played_at)).filter_by(
        user_id=current_user.user_id
    ).scalar()

    return {
        "total_tracks": total_tracks,
        "total_artists": total_artists,
        "last_sync": last_play.isoformat() if last_play else None,
        "etl_status": "success" if total_tracks > 0 else "idle",
    }


@router.get("/genres")
def get_top_genres(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Top géneros del usuario.
    Shape: { genres: [{genre, count, percentage}], total_plays }
    Compatible con GenresResponse del frontend.
    """
    logger.info(f"Obteniendo géneros para {current_user.spotify_id}")

    total_plays = db.query(func.count(FactListeningHistory.id)).filter_by(
        user_id=current_user.user_id
    ).scalar() or 0

    rows = db.query(DimArtists.genres).join(
        FactListeningHistory,
        FactListeningHistory.artist_id == DimArtists.artist_id
    ).filter(
        FactListeningHistory.user_id == current_user.user_id,
        DimArtists.genres.isnot(None)
    ).all()

    genre_counter: Counter = Counter()
    for (genres,) in rows:
        if genres:
            for g in genres:
                if g:
                    genre_counter[g.strip()] += 1

    total_genre_plays = sum(genre_counter.values()) or 1

    genres_list = [
        {
            "genre": genre,
            "count": count,
            "percentage": round(count / total_genre_plays * 100, 1),
        }
        for genre, count in genre_counter.most_common(10)
    ]

    return {"genres": genres_list, "total_plays": total_plays}


@router.get("/peak-hour")
def get_peak_hour(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hora pico del usuario.
    Shape: { hour, play_count, label }
    Compatible con PeakHour del frontend.
    """
    logger.info(f"Obteniendo peak-hour para {current_user.spotify_id}")

    row = db.query(
        FactListeningHistory.hour_of_day,
        func.count(FactListeningHistory.id).label("play_count")
    ).filter(
        FactListeningHistory.user_id == current_user.user_id,
        FactListeningHistory.hour_of_day.isnot(None)
    ).group_by(FactListeningHistory.hour_of_day).order_by(desc("play_count")).first()

    if not row:
        return {"hour": 0, "play_count": 0, "label": "00:00 – 01:00"}

    hour = row[0]
    play_count = row[1]
    end = (hour + 1) % 24
    label = f"{hour:02d}:00 – {end:02d}:00"

    return {"hour": hour, "play_count": play_count, "label": label}