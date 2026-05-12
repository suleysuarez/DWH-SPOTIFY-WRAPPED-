"""
Rutas de datos: artists, tracks, history, profile.
Todos los endpoints requieren JWT válido.
"""

import logging
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from app.core.database import get_db
from app.core.security import verify_jwt_token, extract_bearer_token
from app.models.models import (
    DimUsers, DimArtists, DimTracks, FactListeningHistory
)
from app.schemas.schemas import (
    TopArtistsResponse, ArtistResponse,
    TopTracksResponse, TrackResponse,
    PeakHourResponse, GenresResponse, GenreData,
    QuickStatsResponse, UserProfileResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["data"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> DimUsers:
    """Dependency para verificar JWT y obtener usuario actual."""
    token = extract_bearer_token(authorization)
    payload = verify_jwt_token(token)
    user_id = int(payload["sub"])
    
    user = db.query(DimUsers).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    return user


@router.get("/artists/top", response_model=TopArtistsResponse)
def get_top_artists(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene top 5 artistas del usuario.
    
    Basado en fact_listening_history.
    """
    logger.info(f"Obteniendo top artistas para user_id={current_user.user_id}")
    
    # Query: contar reproducciones por artista
    top_artists = db.query(
        DimArtists,
        func.count(FactListeningHistory.history_id).label("play_count")
    ).join(
        FactListeningHistory,
        FactListeningHistory.artist_id == DimArtists.artist_id
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).group_by(
        DimArtists.artist_id
    ).order_by(
        desc("play_count")
    ).limit(5).all()
    
    artists = [ArtistResponse.from_orm(artist[0]) for artist in top_artists]
    return TopArtistsResponse(artists=artists)


@router.get("/tracks/top", response_model=TopTracksResponse)
def get_top_tracks(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene top 5 canciones del usuario.
    
    Basado en fact_listening_history.
    """
    logger.info(f"Obteniendo top canciones para user_id={current_user.user_id}")
    
    # Query: contar reproducciones por canción
    top_tracks = db.query(
        DimTracks,
        DimArtists.name.label("artist_name"),
        func.count(FactListeningHistory.history_id).label("play_count")
    ).join(
        FactListeningHistory,
        FactListeningHistory.track_id == DimTracks.track_id
    ).join(
        DimArtists,
        DimTracks.artist_id == DimArtists.artist_id
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).group_by(
        DimTracks.track_id, DimArtists.name
    ).order_by(
        desc("play_count")
    ).limit(5).all()
    
    tracks = []
    for track_row in top_tracks:
        track = track_row[0]
        artist_name = track_row[1]
        track_dict = TrackResponse.from_orm(track).dict()
        track_dict["artist_name"] = artist_name
        tracks.append(TrackResponse(**track_dict))
    
    return TopTracksResponse(tracks=tracks)


@router.get("/history/peak-hour", response_model=PeakHourResponse)
def get_peak_hour(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene la hora pico de escucha del usuario.
    
    Basado en EXTRACT(HOUR FROM played_at).
    """
    logger.info(f"Obteniendo hora pico para user_id={current_user.user_id}")
    
    # Query: agrupar por hora y contar
    peak = db.query(
        func.extract("hour", FactListeningHistory.played_at).label("hour"),
        func.count(FactListeningHistory.history_id).label("play_count")
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).group_by(
        "hour"
    ).order_by(
        desc("play_count")
    ).first()
    
    if not peak:
        return PeakHourResponse(hour=0, play_count=0)
    
    return PeakHourResponse(hour=int(peak[0]), play_count=peak[1])


@router.get("/history/genres", response_model=GenresResponse)
def get_genres(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene géneros dominantes del usuario.
    
    Basado en dim_artists.genres (JSON array como string).
    """
    logger.info(f"Obteniendo géneros para user_id={current_user.user_id}")
    
    # Query: contar reproducciones por artista y extraer géneros
    artist_plays = db.query(
        DimArtists.genres,
        func.count(FactListeningHistory.history_id).label("play_count")
    ).join(
        FactListeningHistory,
        FactListeningHistory.artist_id == DimArtists.artist_id
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).group_by(
        DimArtists.artist_id, DimArtists.genres
    ).all()
    
    # Agregar géneros
    genre_counts = {}
    for genres_json, play_count in artist_plays:
        if genres_json:
            try:
                import json
                genres = json.loads(genres_json)
                for genre in genres:
                    genre_counts[genre] = genre_counts.get(genre, 0) + play_count
            except:
                pass
    
    # Top 5 géneros
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    genres = [GenreData(genre=g, count=c) for g, c in sorted_genres]
    
    return GenresResponse(genres=genres)


@router.get("/history/stats", response_model=QuickStatsResponse)
def get_stats(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene estadísticas rápidas del DWH.
    """
    logger.info(f"Obteniendo estadísticas para user_id={current_user.user_id}")
    
    # Total de canciones únicas escuchadas
    total_tracks = db.query(
        func.count(func.distinct(FactListeningHistory.track_id))
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).scalar() or 0
    
    # Total de artistas únicos
    total_artists = db.query(
        func.count(func.distinct(FactListeningHistory.artist_id))
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).scalar() or 0
    
    # Última sincronización (última reproducción registrada)
    last_sync = db.query(
        func.max(FactListeningHistory.created_at)
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).scalar()
    
    return QuickStatsResponse(
        total_tracks=total_tracks,
        total_artists=total_artists,
        last_sync=last_sync,
        etl_status="idle",
    )


@router.get("/profile/me", response_model=UserProfileResponse)
def get_profile(current_user: DimUsers = Depends(get_current_user)):
    """
    Obtiene perfil del usuario autenticado.
    """
    logger.info(f"Obteniendo perfil para user_id={current_user.user_id}")
    
    profile = UserProfileResponse(
        id=current_user.spotify_id,
        spotify_id=current_user.spotify_id,
        display_name=current_user.display_name,
        email=current_user.email,
        country=current_user.country,
        followers=current_user.followers,
        product=current_user.product,
        images=[{"url": current_user.images_url}] if current_user.images_url else None,
    )
    
    return profile
