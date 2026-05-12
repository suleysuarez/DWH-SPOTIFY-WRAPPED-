"""
filename: history.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Schemas Pydantic para historial de escucha.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class HistoryItemResponse(BaseModel):
    """Item de historial."""
    id: int
    user_id: int
    track_id: int
    artist_id: int
    played_at: datetime
    hour_of_day: Optional[int] = None
    day_of_week: Optional[str] = None
    context_type: Optional[str] = None


class HistoryResponse(BaseModel):
    """Response de GET /v1/history/recently-played."""
    items: List[HistoryItemResponse]
    total: int
