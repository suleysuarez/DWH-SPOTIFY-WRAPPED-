"""
Schemas Pydantic para validación de requests/responses.
Convención: Base, Request, Response para cada entidad.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ============ AUTH ============

class AuthLoginResponse(BaseModel):
    """Response de GET /v1/auth/login."""
    authorization_url: str


class AuthCallbackRequest(BaseModel):
    """Request de POST /v1/auth/callback."""
    code: str
    state: str


class AuthCallbackResponse(BaseModel):
    """Response de POST /v1/auth/callback."""
    access_token: str
    token_type: str = "bearer"


# ============ PROFILE ============

class UserProfileBase(BaseModel):
    """Base para usuario."""
    spotify_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    followers: int = 0
    product: str = "free"


class UserProfileResponse(UserProfileBase):
    """Response de GET /v1/profile/me."""
    id: str = None  # Alias para spotify_id
    images: Optional[List[dict]] = None

    class Config:
        from_attributes = True


# ============ ARTISTS ============

class ArtistBase(BaseModel):
    """Base para artista."""
    spotify_id: str
    name: str
    genres: Optional[str] = None
    popularity: Optional[int] = None


class ArtistResponse(ArtistBase):
    """Response de artista."""
    artist_id: int

    class Config:
        from_attributes = True


class TopArtistsResponse(BaseModel):
    """Response de GET /v1/artists/top."""
    artists: List[ArtistResponse]


# ============ TRACKS ============

class TrackBase(BaseModel):
    """Base para canción."""
    spotify_id: str
    name: str
    album_name: Optional[str] = None
    album_image_url: Optional[str] = None
    duration_ms: Optional[int] = None


class TrackResponse(TrackBase):
    """Response de canción."""
    track_id: int
    artist_id: int
    artist_name: Optional[str] = None

    class Config:
        from_attributes = True


class TopTracksResponse(BaseModel):
    """Response de GET /v1/tracks/top."""
    tracks: List[TrackResponse]


# ============ HISTORY ============

class PeakHourResponse(BaseModel):
    """Response de GET /v1/history/peak-hour."""
    hour: int
    play_count: int


class GenreData(BaseModel):
    """Género con conteo."""
    genre: str
    count: int


class GenresResponse(BaseModel):
    """Response de GET /v1/history/genres."""
    genres: List[GenreData]


class QuickStatsResponse(BaseModel):
    """Response de GET /v1/history/stats."""
    total_tracks: int
    total_artists: int
    last_sync: Optional[datetime] = None
    etl_status: str = "idle"


# ============ ETL ============

class DwhTable(BaseModel):
    """Información de tabla en el DWH."""
    table_name: str
    record_count: int
    last_sync: Optional[datetime] = None
    status: str  # 'loaded', 'empty', 'stale'


class EtlRun(BaseModel):
    """Ejecución ETL."""
    id: int
    started_at: datetime
    duration_seconds: Optional[int] = None
    records_extracted: int
    records_loaded: int
    status: str  # 'success', 'error', 'running'


class EtlStatusResponse(BaseModel):
    """Response de GET /v1/etl/status."""
    tables: List[DwhTable]
    recent_runs: List[EtlRun]


class EtlRunResponse(BaseModel):
    """Response de POST /v1/etl/run."""
    status: str  # 'started', 'success', 'error'
    message: Optional[str] = None
    logs: Optional[List[str]] = None
