"""
filename: search.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-22
version: 1.0
description: Búsqueda de artistas y canciones dentro del DWH del usuario.
             GET /search?q=term&type=all|artist|track
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.models.models import DimUsers, DimArtists, DimTracks, FactListeningHistory
from app.v1.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> DimUsers:
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


@router.get("")
def search(
    q: str = Query(..., min_length=1, max_length=100),
    type: Optional[str] = Query("all", pattern="^(all|artist|track)$"),
    limit: int = Query(8, ge=1, le=20),
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    term = f"%{q.strip()}%"
    artists_out = []
    tracks_out = []

    if type in ("all", "artist"):
        rows = (
            db.query(
                DimArtists.artist_id,
                DimArtists.spotify_id,
                DimArtists.name,
                DimArtists.image_url,
                DimArtists.genres,
                DimArtists.popularity,
                DimArtists.followers_count,
                func.count(FactListeningHistory.id).label("play_count"),
            )
            .join(FactListeningHistory, FactListeningHistory.artist_id == DimArtists.artist_id)
            .filter(
                FactListeningHistory.user_id == current_user.user_id,
                DimArtists.name.ilike(term),
            )
            .group_by(
                DimArtists.artist_id,
                DimArtists.spotify_id,
                DimArtists.name,
                DimArtists.image_url,
                DimArtists.genres,
                DimArtists.popularity,
                DimArtists.followers_count,
            )
            .order_by(desc("play_count"))
            .limit(limit)
            .all()
        )
        for r in rows:
            artists_out.append({
                "artist_id": r.artist_id,
                "spotify_id": r.spotify_id,
                "name": r.name,
                "image_url": r.image_url,
                "genres": r.genres or [],
                "popularity": r.popularity,
                "followers_count": r.followers_count,
                "play_count": r.play_count,
            })

    if type in ("all", "track"):
        rows = (
            db.query(
                DimTracks.track_id,
                DimTracks.spotify_id,
                DimTracks.name,
                DimTracks.album_name,
                DimTracks.album_image_url,
                DimTracks.duration_ms,
                DimTracks.popularity,
                DimArtists.name.label("artist_name"),
                DimArtists.image_url.label("artist_image_url"),
                func.count(FactListeningHistory.id).label("play_count"),
            )
            .join(DimArtists, DimTracks.artist_id == DimArtists.artist_id)
            .join(FactListeningHistory, FactListeningHistory.track_id == DimTracks.track_id)
            .filter(
                FactListeningHistory.user_id == current_user.user_id,
                DimTracks.name.ilike(term),
            )
            .group_by(
                DimTracks.track_id,
                DimTracks.spotify_id,
                DimTracks.name,
                DimTracks.album_name,
                DimTracks.album_image_url,
                DimTracks.duration_ms,
                DimTracks.popularity,
                DimArtists.name,
                DimArtists.image_url,
            )
            .order_by(desc("play_count"))
            .limit(limit)
            .all()
        )
        for r in rows:
            tracks_out.append({
                "track_id": r.track_id,
                "spotify_id": r.spotify_id,
                "name": r.name,
                "album_name": r.album_name,
                "album_image_url": r.album_image_url,
                "duration_ms": r.duration_ms,
                "popularity": r.popularity,
                "artist_name": r.artist_name,
                "artist_image_url": r.artist_image_url,
                "play_count": r.play_count,
            })

    return {
        "q": q,
        "artists": artists_out,
        "tracks": tracks_out,
        "total": len(artists_out) + len(tracks_out),
    }
