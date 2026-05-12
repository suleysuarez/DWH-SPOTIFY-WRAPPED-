"""
filename: tracks.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Schemas Pydantic para canciones.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TrackBase(BaseModel):
    """Base para canción."""
    spotify_id: str
    name: str
    album_name: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = None
    explicit: bool = False


class TrackResponse(TrackBase):
    """Response de canción."""
    track_id: int
    artist_id: int
    loaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TracksResponse(BaseModel):
    """Response de GET /v1/tracks/top."""
    items: List[TrackResponse]
