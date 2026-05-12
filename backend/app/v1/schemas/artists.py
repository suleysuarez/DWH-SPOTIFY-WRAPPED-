"""
filename: artists.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Schemas Pydantic para artistas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ArtistBase(BaseModel):
    """Base para artista."""
    spotify_id: str
    name: str
    popularity: Optional[int] = None
    followers_count: Optional[int] = None
    genres: Optional[List[str]] = None


class ArtistResponse(ArtistBase):
    """Response de artista."""
    artist_id: int
    loaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtistsResponse(BaseModel):
    """Response de GET /v1/artists/top."""
    items: List[ArtistResponse]
