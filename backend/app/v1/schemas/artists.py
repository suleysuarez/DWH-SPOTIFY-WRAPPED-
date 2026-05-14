"""
filename: artists.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Schemas Pydantic para artistas.
"""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator


class ArtistResponse(BaseModel):
    """
    Response de artista.
    Shape compatible con el tipo Artist del frontend:
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
        if hasattr(data, "spotify_id"):
            spotify_id = getattr(data, "spotify_id", None)
            return {
                "id": spotify_id,
                "name": getattr(data, "name", ""),
                "popularity": getattr(data, "popularity", None),
                "genres": getattr(data, "genres", []) or [],
                "images": [],
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