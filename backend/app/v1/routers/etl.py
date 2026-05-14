"""
filename: etl.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.1
description: Rutas ETL. Endpoints: POST /v1/etl/run, GET /v1/etl/status, GET /v1/etl/history.
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
from app.models.models import DimUsers, EtlAudit, FactListeningHistory, DimArtists, DimTracks
from app.v1.services.auth_service import AuthService
from app.v1.services.etl_service import EtlService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/etl", tags=["etl"])
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> DimUsers:
    """Valida JWT y retorna usuario actual."""
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
    """Ejecuta el pipeline ETL completo."""
    logger.info(f"Iniciando ETL para {current_user.spotify_id}")

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
        user_data = EtlService.extract_user(current_user.spotify_access_token)
        artists_data = EtlService.extract_top_artists(current_user.spotify_access_token)
        tracks_data = EtlService.extract_top_tracks(current_user.spotify_access_token)

        last_audit = db.query(EtlAudit).filter_by(
            spotify_user_id=current_user.spotify_id,
            status="success"
        ).order_by(desc(EtlAudit.started_at)).first()

        cursor_after_ms = last_audit.cursor_next_ms if last_audit else None
        history_data, cursor_next_ms = EtlService.extract_recently_played(
            current_user.spotify_access_token,
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
    """Obtiene estado actual del DWH y ultimas 5 ejecuciones ETL."""
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
    Historial completo de ejecuciones ETL con paginacion y filtro por status.
    Query params:
      - status: 'success' | 'error' | 'running' (opcional)
      - limit: cuantos traer (default 20)
      - offset: desde donde (default 0)
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