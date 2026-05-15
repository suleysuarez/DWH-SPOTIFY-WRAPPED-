"""
filename: tracks.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Schemas Pydantic para el recurso canciones. TrackBase define los campos del DWH,
             TrackRequest los campos de entrada, TrackResponse adapta el ORM al shape del
             frontend (spotify_id → id, album_image_url → album_image) y TracksResponse pagina.
"""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator


class TrackBase(BaseModel):
    """Campos base de la canción tal como se almacenan en dwh.dim_tracks."""

    spotify_id: str
    name: str
    album_name: Optional[str] = None
    album_image_url: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = None
    explicit: bool = False


class TrackRequest(TrackBase):
    """
    Request para registrar o actualizar una canción en el DWH.

    Extiende TrackBase con el identificador del artista principal.
    Utilizado internamente por el ETL; no hay endpoint público de escritura para tracks.
    """

    spotify_artist_id: str


class TrackResponse(BaseModel):
    """
    Respuesta de canción.

    Shape compatible con el tipo Track del frontend (types/track.ts):
      { id, name, artist_name, album_name, duration_ms, popularity,
        preview_url, external_urls, album_image, play_count, rank }
    """

    id: str
    name: str
    artist_name: str = ""
    album_name: Optional[str] = None
    duration_ms: Optional[int] = 0
    popularity: Optional[int] = None
    preview_url: Optional[str] = None
    external_urls: dict = {}
    album_image: Optional[str] = None
    play_count: Optional[int] = None
    rank: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def map_fields(cls, data):
        """Mapea los campos del ORM al shape que espera el frontend."""
        if hasattr(data, "spotify_id"):
            spotify_id = getattr(data, "spotify_id", None)
            artist_name = getattr(data, "artist_name", "")
            return {
                "id": spotify_id,
                "name": getattr(data, "name", ""),
                "artist_name": artist_name,
                "album_name": getattr(data, "album_name", None),
                "duration_ms": getattr(data, "duration_ms", 0) or 0,
                "popularity": getattr(data, "popularity", None),
                "preview_url": None,
                "external_urls": {
                    "spotify": f"https://open.spotify.com/track/{spotify_id}"
                } if spotify_id else {},
                "album_image": getattr(data, "album_image_url", None),
                "play_count": getattr(data, "play_count", None),
                "rank": getattr(data, "rank", None),
            }
        return data


class TracksResponse(BaseModel):
    """Response de GET /v1/tracks/top — compatible con TopTracksResponse del frontend."""

    tracks: List[TrackResponse]
    total: int
