"""
filename: models.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Modelos SQLAlchemy para el star schema del DWH. Tablas: dim_users, dim_artists, dim_tracks, fact_listening_history, etl_audit, pkce_sessions.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean, ARRAY, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DimUsers(Base):
    """Dimensión de usuarios de Spotify."""
    __tablename__ = "dim_users"
    __table_args__ = {"schema": "dwh"}

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    country = Column(String(10), nullable=True)
    followers = Column(Integer, default=0)
    product = Column(String(20), default="free")  # 'free' o 'premium'
    spotify_access_token = Column(Text, nullable=False)
    spotify_refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    loaded_at = Column(DateTime, default=func.now())


class DimArtists(Base):
    """Dimensión de artistas."""
    __tablename__ = "dim_artists"
    __table_args__ = {"schema": "dwh"}

    artist_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    popularity = Column(Integer, nullable=True)
    followers_count = Column(Integer, nullable=True)
    genres = Column(ARRAY(String), nullable=True)  # TEXT[] nativo de PostgreSQL
    loaded_at = Column(DateTime, default=func.now())


class DimTracks(Base):
    """Dimensión de canciones."""
    __tablename__ = "dim_tracks"
    __table_args__ = {"schema": "dwh"}

    track_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    artist_id = Column(Integer, ForeignKey("dwh.dim_artists.artist_id"), nullable=False)
    album_name = Column(String(255), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    popularity = Column(Integer, nullable=True)
    explicit = Column(Boolean, default=False)
    loaded_at = Column(DateTime, default=func.now())


class FactListeningHistory(Base):
    """Tabla de hechos: historial de escucha."""
    __tablename__ = "fact_listening_history"
    __table_args__ = (
        {"schema": "dwh"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("dwh.dim_users.user_id"), nullable=False, index=True)
    track_id = Column(Integer, ForeignKey("dwh.dim_tracks.track_id"), nullable=False)
    artist_id = Column(Integer, ForeignKey("dwh.dim_artists.artist_id"), nullable=False)
    played_at = Column(DateTime, nullable=False, index=True)
    hour_of_day = Column(Integer, nullable=True)  # 0-23
    day_of_week = Column(String(10), nullable=True)  # "Monday", "Tuesday", etc.
    context_type = Column(String(50), nullable=True)  # 'playlist', 'album', etc.


class EtlAudit(Base):
    """Auditoría de ejecuciones ETL."""
    __tablename__ = "etl_audit"
    __table_args__ = {"schema": "dwh"}

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_user_id = Column(String(100), nullable=False)  # ID antes de resolver FK
    started_at = Column(DateTime, nullable=False, default=func.now())
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)  # 'success', 'error'
    error_message = Column(Text, nullable=True)
    users_new = Column(Integer, default=0)
    artists_new = Column(Integer, default=0)
    artists_skipped = Column(Integer, default=0)
    tracks_new = Column(Integer, default=0)
    tracks_skipped = Column(Integer, default=0)
    history_new = Column(Integer, default=0)
    history_skipped = Column(Integer, default=0)
    cursor_after_ms = Column(String(50), nullable=True)  # Cursor usado en esta ejecución
    cursor_next_ms = Column(String(50), nullable=True)  # Cursor para próxima ejecución


class PkceSessions(Base):
    """Sesiones PKCE para OAuth."""
    __tablename__ = "pkce_sessions"
    __table_args__ = {"schema": "public"}

    state = Column(String(128), primary_key=True)
    verifier = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
