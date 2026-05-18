"""
filename: etl.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Router del pipeline ETL. Expone POST /run (ejecuta Extract→Transform→Load),
             GET /status (estado del DWH) y GET /history (historial paginado). Requiere JWT.
"""

import logging
import time
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.core.config import settings
from app.models.models import DimUsers, EtlAudit, FactListeningHistory, DimArtists, DimTracks
from app.v1.services.auth_service import AuthService
from app.v1.services.etl_service import EtlService
from app.v1.services.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/etl", tags=["etl"])
bearer_scheme = HTTPBearer()




async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> DimUsers:
    """
    Dependencia FastAPI: valida el JWT Bearer y retorna el registro DimUsers.

    Args:
        credentials (HTTPAuthorizationCredentials): Token Bearer extraído del header Authorization.
        db (Session): Sesión de SQLAlchemy inyectada por get_db.

    Returns:
        DimUsers: Instancia ORM del usuario autenticado.

    Raises:
        HTTPException: 401 si el token es inválido, expirado o el usuario no existe en BD.
    """
    try:
        payload = AuthService.verify_jwt_token(credentials.credentials)
        spotify_id: str = payload.get("sub")
        if not spotify_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = db.query(DimUsers).filter_by(spotify_id=spotify_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user


@router.post("/run")
def run_etl(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ejecuta el pipeline ETL completo: Extract → Transform → Load.

    Usa el access token almacenado del usuario para llamar a Spotify API.
    La sincronización es incremental: usa cursor_next_ms del último audit exitoso
    como parámetro `after` en recently_played para no reprocesar historial antiguo.

    Args:
        current_user (DimUsers): Usuario autenticado via JWT; su access token se usa para Spotify.
        db (Session): Sesión de SQLAlchemy.

    Returns:
        dict: { status: 'success'|'error', message, logs: [str] } con log detallado de la ejecución.
    """
    logger.info(f"Iniciando ETL para {current_user.spotify_id}")

    # Renovar el access token antes de cada ETL para evitar 401s en sesiones
    # inactivas >1 hora (Spotify expira los tokens en 3600 segundos).
    access_token = current_user.spotify_access_token
    if current_user.spotify_refresh_token:
        try:
            new_tokens = SpotifyClient.refresh_access_token(
                current_user.spotify_refresh_token,
                settings.SPOTIFY_CLIENT_ID,
                settings.SPOTIFY_CLIENT_SECRET,
            )
            access_token = new_tokens["access_token"]
            current_user.spotify_access_token = access_token
            db.commit()
            logger.info("Access token de Spotify renovado exitosamente")
        except Exception as refresh_err:
            logger.warning(f"Token refresh fallido ({refresh_err}), usando token existente")

    audit = EtlAudit(
        spotify_user_id=current_user.spotify_id,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()

    logs = []
    t0 = time.time()

    try:
        logs.append("Extrayendo datos de Spotify...")
        user_data = EtlService.extract_user(access_token)
        artists_data = EtlService.extract_top_artists(access_token)
        tracks_data = EtlService.extract_top_tracks(access_token)

        last_audit = db.query(EtlAudit).filter_by(
            spotify_user_id=current_user.spotify_id,
            status="success"
        ).order_by(desc(EtlAudit.started_at)).first()

        cursor_after_ms = last_audit.cursor_next_ms if last_audit else None
        history_data, cursor_next_ms = EtlService.extract_recently_played(
            access_token,
            after=cursor_after_ms
        )

        logs.append(f"Extraido: {len(artists_data)} artistas, {len(tracks_data)} canciones, {len(history_data)} historial")

        logs.append("Transformando datos...")
        user_transformed = EtlService.transform_user(user_data)
        artists_transformed = EtlService.transform_artists(artists_data)
        tracks_transformed = EtlService.transform_tracks(tracks_data)
        history_transformed = EtlService.transform_history(history_data)
        logs.append("Datos transformados exitosamente")

        logs.append("Cargando datos en DWH...")
        EtlService.load_user(db, user_transformed, current_user.spotify_access_token, current_user.spotify_refresh_token)
        artists_new, artists_skipped = EtlService.load_artists(db, artists_transformed)
        tracks_new, tracks_skipped = EtlService.load_tracks(db, tracks_transformed)
        history_new, history_skipped = EtlService.load_history(db, current_user.spotify_id, history_transformed)

        genres_updated = EtlService.backfill_artist_genres(db)
        if genres_updated:
            logs.append(f"Géneros enriquecidos con Last.fm: {genres_updated} artistas actualizados")

        logs.append(f"Cargado: {artists_new} artistas nuevos, {tracks_new} canciones nuevas, {history_new} historial nuevo")

        duration_ms = int((time.time() - t0) * 1000)
        audit.status = "success"
        audit.finished_at = datetime.utcnow()
        audit.duration_ms = duration_ms
        audit.users_new = 1
        audit.artists_new = artists_new
        audit.artists_skipped = artists_skipped
        audit.tracks_new = tracks_new
        audit.tracks_skipped = tracks_skipped
        audit.history_new = history_new
        audit.history_skipped = history_skipped
        audit.cursor_after_ms = cursor_after_ms
        audit.cursor_next_ms = cursor_next_ms
        db.commit()

        logger.info(f"ETL completado exitosamente en {duration_ms}ms")

        return {
            "status": "success",
            "message": "ETL completado exitosamente",
            "logs": logs,
        }

    except Exception as e:
        logger.error(f"Error en ETL: {e}", exc_info=True)

        duration_ms = int((time.time() - t0) * 1000)
        audit.status = "error"
        audit.finished_at = datetime.utcnow()
        audit.duration_ms = duration_ms
        audit.error_message = str(e)
        db.commit()

        return {
            "status": "error",
            "message": str(e),
            "logs": logs + [f"Error: {str(e)}"],
        }


@router.get("/status")
def get_etl_status(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene el estado actual del DWH y las últimas 5 ejecuciones ETL del usuario.

    Args:
        current_user (DimUsers): Usuario autenticado via JWT.
        db (Session): Sesión de SQLAlchemy.

    Returns:
        dict: { tables: [{table_name, record_count, status}], recent_runs: [{id, started_at,
               duration_seconds, records_extracted, records_loaded, status, error_message}] }
    """
    logger.info(f"Obteniendo estado ETL para {current_user.spotify_id}")

    tables = []

    artist_count = db.query(func.count(DimArtists.artist_id)).scalar() or 0
    tables.append({
        "table_name": "dim_artists",
        "record_count": artist_count,
        "status": "loaded" if artist_count > 0 else "empty",
    })

    track_count = db.query(func.count(DimTracks.track_id)).scalar() or 0
    tables.append({
        "table_name": "dim_tracks",
        "record_count": track_count,
        "status": "loaded" if track_count > 0 else "empty",
    })

    history_count = db.query(
        func.count(FactListeningHistory.id)
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).scalar() or 0
    tables.append({
        "table_name": "fact_listening_history",
        "record_count": history_count,
        "status": "loaded" if history_count > 0 else "empty",
    })

    recent_audits = db.query(EtlAudit).filter_by(
        spotify_user_id=current_user.spotify_id
    ).order_by(
        desc(EtlAudit.started_at)
    ).limit(5).all()

    runs = [
        {
            "id": audit.audit_id,
            "started_at": audit.started_at.isoformat() + "+00:00",
            "duration_seconds": audit.duration_ms // 1000 if audit.duration_ms else None,
            "records_extracted": (audit.artists_new or 0) + (audit.tracks_new or 0) + (audit.history_new or 0),
            "records_loaded": (audit.artists_new or 0) + (audit.tracks_new or 0) + (audit.history_new or 0),
            "status": audit.status,
            "error_message": audit.error_message,
        }
        for audit in recent_audits
    ]

    return {
        "tables": tables,
        "recent_runs": runs,
    }


@router.get("/history")
def get_etl_history(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Historial paginado de ejecuciones ETL del usuario con filtro opcional por estado.

    Args:
        status_filter (Optional[str]): Filtro por estado: 'success', 'error' o 'running'.
        limit (int): Número máximo de registros a retornar (1-100, default 20).
        offset (int): Índice de inicio para paginación (default 0).
        current_user (DimUsers): Usuario autenticado via JWT.
        db (Session): Sesión de SQLAlchemy.

    Returns:
        dict: { runs: [EtlAudit serializado], total, limit, offset, has_more }
    """
    logger.info(f"Obteniendo historial ETL para {current_user.spotify_id}")

    query = db.query(EtlAudit).filter_by(spotify_user_id=current_user.spotify_id)

    if status_filter and status_filter in ("success", "error", "running"):
        query = query.filter(EtlAudit.status == status_filter)

    total = query.count()

    audits = query.order_by(desc(EtlAudit.started_at)).offset(offset).limit(limit).all()

    runs = [
        {
            "id": audit.audit_id,
            "started_at": audit.started_at.isoformat() + "+00:00",
            "finished_at": audit.finished_at.isoformat() + "+00:00" if audit.finished_at else None,
            "duration_seconds": audit.duration_ms // 1000 if audit.duration_ms else None,
            "status": audit.status,
            "error_message": audit.error_message,
            "artists_new": audit.artists_new or 0,
            "tracks_new": audit.tracks_new or 0,
            "history_new": audit.history_new or 0,
            "history_skipped": audit.history_skipped or 0,
        }
        for audit in audits
    ]

    return {
        "runs": runs,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
    }


@router.get("/{run_id}/tracks")
def get_etl_run_tracks(
    run_id: int,
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna las canciones insertadas en dim_tracks durante una ejecución ETL específica.

    Usa el rango started_at → finished_at del audit para filtrar por loaded_at en dim_tracks.

    Args:
        run_id (int): audit_id de la ejecución ETL.
        current_user (DimUsers): Usuario autenticado via JWT.
        db (Session): Sesión de SQLAlchemy.

    Returns:
        dict: { tracks: [{name, artist_name, album_name, album_image_url, duration_ms, popularity}], total }

    Raises:
        HTTPException: 404 si el run_id no existe o no pertenece al usuario.
    """
    audit = db.query(EtlAudit).filter_by(
        audit_id=run_id,
        spotify_user_id=current_user.spotify_id,
    ).first()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada")

    if not audit.finished_at:
        return {"tracks": [], "total": 0}

    rows = (
        db.query(DimTracks, DimArtists.name.label("artist_name"))
        .join(DimArtists, DimTracks.artist_id == DimArtists.artist_id)
        .filter(
            DimTracks.loaded_at >= audit.started_at,
            DimTracks.loaded_at <= audit.finished_at,
        )
        .order_by(DimTracks.loaded_at)
        .all()
    )

    tracks = [
        {
            "name": row.DimTracks.name,
            "artist_name": row.artist_name,
            "album_name": row.DimTracks.album_name,
            "album_image_url": row.DimTracks.album_image_url,
            "duration_ms": row.DimTracks.duration_ms,
            "popularity": row.DimTracks.popularity,
        }
        for row in rows
    ]

    return {"tracks": tracks, "total": len(tracks)}