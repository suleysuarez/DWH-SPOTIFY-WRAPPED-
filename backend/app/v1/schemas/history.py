"""
filename: history.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Schemas Pydantic para el recurso historial. HistoryItemBase define los campos
             temporales de reproducción, HistoryItemCreate los campos de inserción,
             HistoryItemResponse la salida del endpoint y HistoryResponse la lista paginada.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class HistoryItemBase(BaseModel):
    """Campos base de un registro de reproducción (dimensiones temporales)."""

    played_at: datetime
    hour_of_day: Optional[int] = None
    day_of_week: Optional[str] = None
    context_type: Optional[str] = None


class HistoryItemCreate(HistoryItemBase):
    """
    Request para insertar un registro en fact_listening_history.

    Extiende HistoryItemBase con las claves foráneas internas del DWH.
    Usado internamente por EtlService.load_history; no hay endpoint público de escritura.
    """

    user_id: int
    track_id: int
    artist_id: int


class HistoryItemResponse(HistoryItemBase):
    """Item de historial serializado desde fact_listening_history."""

    id: int
    user_id: int
    track_id: int
    artist_id: int

    model_config = ConfigDict(from_attributes=True)


class HistoryResponse(BaseModel):
    """Response de GET /v1/history/recently-played — lista paginada de reproducciones."""

    items: List[HistoryItemResponse]
    total: int
