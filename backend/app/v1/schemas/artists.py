"""
filename: artists.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Schemas Pydantic para el recurso artistas. ArtistBase define los campos del DWH,
             ArtistRequest los campos de entrada, ArtistResponse adapta el ORM al shape del
             frontend (spotify_id → id, image_url → images[]) y ArtistsResponse pagina la lista.
"""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator


class ArtistBase(BaseModel):
    """Campos base del artista tal como se almacenan en dwh.dim_artists."""

    spotify_id: str
    name: str
    popularity: Optional[int] = None
    followers_count: Optional[int] = None
    genres: Optional[List[str]] = []
    image_url: Optional[str] = None


class ArtistRequest(ArtistBase):
    """
    Request para registrar o actualizar un artista en el DWH.

    Hereda todos los campos de ArtistBase. Utilizado internamente por el ETL;
    no hay endpoint público de escritura para artistas.
    """

    pass


class ArtistResponse(BaseModel):
    """
    Respuesta de artista individual.

    Shape compatible con el tipo Artist del frontend (types/artist.ts):
      { id, name, popularity, genres, images, external_urls, play_count, rank }
    """

    id: str
    name: str
    popularity: Optional[int] = None
    genres: Optional[List[str]] = []
    images: List[dict] = []
    external_urls: dict = {}
    play_count: Optional[int] = None
    rank: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def map_fields(cls, data):
        """Mapea campos del ORM DimArtists al shape que espera el frontend."""
        if hasattr(data, "spotify_id"):
            spotify_id = getattr(data, "spotify_id", None)
            image_url = getattr(data, "image_url", None)
            images = [{"url": image_url}] if image_url else []
            return {
                "id": spotify_id,
                "name": getattr(data, "name", ""),
                "popularity": getattr(data, "popularity", None),
                "genres": getattr(data, "genres", []) or [],
                "images": images,
                "external_urls": {
                    "spotify": f"https://open.spotify.com/artist/{spotify_id}"
                } if spotify_id else {},
                "play_count": getattr(data, "play_count", None),
                "rank": getattr(data, "rank", None),
            }
        return data


class ArtistsResponse(BaseModel):
    """Response de GET /v1/artists/top — compatible con TopArtistsResponse del frontend."""

    artists: List[ArtistResponse]
    total: int
