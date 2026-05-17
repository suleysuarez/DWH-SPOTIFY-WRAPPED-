"""
filename: models.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Modelos SQLAlchemy del star schema del DWH. Define DimUsers, DimArtists,
             DimTracks, FactListeningHistory y EtlAudit (schema dwh) y PkceSessions (public).
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean, ARRAY, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DimUsers(Base):
    """
    Dimensión de usuarios de Spotify (dwh.dim_users).

    Almacena el perfil y los tokens OAuth de cada usuario autenticado.
    El access token se usa en cada ejecución ETL para llamar a la API de Spotify.
    El campo spotify_id es la clave de negocio (único en Spotify) y se usa como
    identificador en el payload JWT.
    """
    __tablename__ = "dim_users"
    __table_args__ = {"schema": "dwh"}

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    country = Column(String(10), nullable=True)
    followers = Column(Integer, default=0)
    product = Column(String(20), default="free")
    image_url = Column(Text, nullable=True)
    spotify_access_token = Column(Text, nullable=False)
    spotify_refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    loaded_at = Column(DateTime, default=func.now())


class DimArtists(Base):
    """
    Dimensión de artistas (dwh.dim_artists).

    Poblada durante el ETL desde el endpoint `/me/top/artists` de Spotify.
    `genres` es un ARRAY de strings PostgreSQL; SQLAlchemy requiere llamar
    `flag_modified(obj, "genres")` después de mutar la lista para que detecte
    el cambio. `image_url` almacena la primera imagen de mayor resolución.
    """
    __tablename__ = "dim_artists"
    __table_args__ = {"schema": "dwh"}

    artist_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    popularity = Column(Integer, nullable=True)
    followers_count = Column(Integer, nullable=True)
    genres = Column(ARRAY(String), nullable=True)
    image_url = Column(Text, nullable=True)  # Foto del artista desde Spotify
    loaded_at = Column(DateTime, default=func.now())


class DimTracks(Base):
    """
    Dimensión de canciones (dwh.dim_tracks).

    Poblada durante el ETL desde el endpoint `/me/top/tracks` de Spotify.
    Cada track apunta a un artista principal vía `artist_id`. Si el artista
    no existe aún en dim_artists, el ETL crea un registro mínimo antes del insert.
    `album_image_url` almacena la portada del álbum para mostrar en el dashboard.
    """
    __tablename__ = "dim_tracks"
    __table_args__ = {"schema": "dwh"}

    track_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    artist_id = Column(Integer, ForeignKey("dwh.dim_artists.artist_id"), nullable=False)
    album_name = Column(String(255), nullable=True)
    album_image_url = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    popularity = Column(Integer, nullable=True)
    explicit = Column(Boolean, default=False)
    loaded_at = Column(DateTime, default=func.now())


class FactListeningHistory(Base):
    """
    Tabla de hechos: historial de escucha (dwh.fact_listening_history).

    Cada fila representa una reproducción de una canción por un usuario.
    `hour_of_day` (0-23) y `day_of_week` ("Monday"…"Sunday") se calculan
    durante la fase Transform del ETL a partir de `played_at`.
    `context_type` puede ser "playlist", "album", "artist" o "unknown".

    Deduplicación: antes de insertar se verifica (user_id, track_id, played_at).
    La migración 001 crea además una UniqueConstraint(user_id, played_at).
    """
    __tablename__ = "fact_listening_history"
    __table_args__ = (
        {"schema": "dwh"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("dwh.dim_users.user_id"), nullable=False, index=True)
    track_id = Column(Integer, ForeignKey("dwh.dim_tracks.track_id"), nullable=False)
    artist_id = Column(Integer, ForeignKey("dwh.dim_artists.artist_id"), nullable=False)
    played_at = Column(DateTime, nullable=False, index=True)
    hour_of_day = Column(Integer, nullable=True)
    day_of_week = Column(String(10), nullable=True)
    context_type = Column(String(50), nullable=True)


class EtlAudit(Base):
    """
    Auditoría de ejecuciones ETL (dwh.etl_audit).

    Registra cada llamada a POST /v1/etl/run con métricas de rendimiento
    y contadores por entidad (artistas, canciones, historial nuevos/saltados).
    `status` puede ser "running" (durante la ejecución), "success" o "error".
    `cursor_next_ms` guarda el cursor de paginación de Spotify para sincronización
    incremental: el siguiente ETL lo usará como parámetro `after`.
    """
    __tablename__ = "etl_audit"
    __table_args__ = {"schema": "dwh"}

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_user_id = Column(String(100), nullable=False)
    started_at = Column(DateTime, nullable=False, default=func.now())
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    users_new = Column(Integer, default=0)
    artists_new = Column(Integer, default=0)
    artists_skipped = Column(Integer, default=0)
    tracks_new = Column(Integer, default=0)
    tracks_skipped = Column(Integer, default=0)
    history_new = Column(Integer, default=0)
    history_skipped = Column(Integer, default=0)
    cursor_after_ms = Column(String(50), nullable=True)
    cursor_next_ms = Column(String(50), nullable=True)


class PkceSessions(Base):
    """
    Sesiones PKCE temporales para el flujo OAuth (public.pkce_sessions).

    Se crea un registro por cada solicitud GET /v1/auth/login, con el `state`
    como PK y el `code_verifier` para verificar el callback de Spotify.
    El registro se elimina inmediatamente tras un callback exitoso para evitar
    reutilización del state. No tiene TTL automático (limpieza manual si fuera necesario).
    """
    __tablename__ = "pkce_sessions"
    __table_args__ = {"schema": "public"}

    state = Column(String(128), primary_key=True)
    verifier = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
