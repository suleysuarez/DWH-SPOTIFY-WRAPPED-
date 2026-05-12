"""
Modelos SQLAlchemy para el star schema del DWH.
Tablas: dim_users, dim_artists, dim_tracks, fact_listening_history, etl_audit, pkce_sessions.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class DimUsers(Base):
    """Dimensión de usuarios de Spotify."""
    __tablename__ = "dim_users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    country = Column(String(10), nullable=True)
    followers = Column(Integer, default=0)
    product = Column(String(20), default="free")  # 'free' o 'premium'
    images_url = Column(String(500), nullable=True)  # URL del avatar
    spotify_access_token = Column(Text, nullable=False)  # Encriptado en producción
    spotify_refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DimArtists(Base):
    """Dimensión de artistas."""
    __tablename__ = "dim_artists"

    artist_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    genres = Column(String(500), nullable=True)  # JSON array como string
    popularity = Column(Integer, nullable=True)
    images_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())


class DimTracks(Base):
    """Dimensión de canciones."""
    __tablename__ = "dim_tracks"

    track_id = Column(Integer, primary_key=True, autoincrement=True)
    spotify_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    artist_id = Column(Integer, ForeignKey("dim_artists.artist_id"), nullable=False)
    album_name = Column(String(255), nullable=True)
    album_image_url = Column(String(500), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    explicit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class FactListeningHistory(Base):
    """Tabla de hechos: historial de escucha."""
    __tablename__ = "fact_listening_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("dim_users.user_id"), nullable=False, index=True)
    track_id = Column(Integer, ForeignKey("dim_tracks.track_id"), nullable=False)
    artist_id = Column(Integer, ForeignKey("dim_artists.artist_id"), nullable=False)
    played_at = Column(DateTime, nullable=False, index=True)
    context_type = Column(String(50), nullable=True)  # 'playlist', 'album', etc.
    context_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())


class EtlAudit(Base):
    """Auditoría de ejecuciones ETL."""
    __tablename__ = "etl_audit"

    etl_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("dim_users.user_id"), nullable=False)
    status = Column(String(20), default="pending")  # 'pending', 'running', 'success', 'error'
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    records_extracted = Column(Integer, default=0)
    records_loaded = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    cursor_next_ms = Column(String(50), nullable=True)  # Cursor para próxima ejecución
    logs = Column(Text, nullable=True)  # JSON array de logs


class PkceSessions(Base):
    """Sesiones PKCE para OAuth."""
    __tablename__ = "pkce_sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String(100), unique=True, nullable=False, index=True)
    code_verifier = Column(String(128), nullable=False)
    code_challenge = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
