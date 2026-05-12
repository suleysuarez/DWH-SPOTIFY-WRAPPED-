"""
filename: profile.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Schemas Pydantic para perfil de usuario.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProfileBase(BaseModel):
    """Base para perfil de usuario."""
    spotify_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    followers: int = 0
    product: str = "free"


class ProfileResponse(ProfileBase):
    """Response de GET /v1/profile/me."""
    user_id: int
    loaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
