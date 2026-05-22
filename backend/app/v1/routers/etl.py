"""
filename: etl.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Router del pipeline ETL. Expone POST /run (ejecuta Extract→Transform→Load),
             GET /status (estado del DWH) y GET /history (historial paginado). Requiere JWT.
             ETL full (géneros + stats) se ejecuta automáticamente una vez por semana (lunes-domingo).
             El resto de días corre ETL incremental (solo historial y nuevos artistas/tracks).
"""

import logging
import time
from datetime import datetime, timedelta
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
    Ejecuta el pipeline ETL.

    - ETL FULL (lunes o primera ejecución de la semana):
        Extrae artistas, tracks e historial.
        Recalcula géneros, popularity y followers desde Last.fm.

    - ETL INCREMENTAL (martes a domingo, si ya hubo full esta semana):
        Solo extrae historial nuevo y artistas/tracks nuevos.
        No recalcula géneros ni stats de artistas ya existentes.
    """
    logger.info(f"Iniciando ETL para {current_user.spotify_id}")

    # ── Determinar si es ETL full o incremental ──────────────────────────────
    # Full si: es lunes, o no hubo ningún ETL exitoso esta semana.
    today = datetime.utcnow()
    monday = today - timedelta(days=today.weekday())
    monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    recent_success = db.query(EtlAudit).filter(
        EtlAudit.spotify_user_id == current_user.spotify_id,
        EtlAudit.status == "success",
        EtlAudit.started_at >= monday_start,
    ).order_by(desc(EtlAudit.started_at)).first()

    is_full_run = (recent_success is None) or (today.weekday() == 0)
    run_type = "FULL" if is_full_run else "INCREMENTAL"
    logger.info(f"Tipo de ETL: {run_type}")

    # ── Renovar access token ─────────────────────────────────────────────────
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
        is_full_run=is_full_run,
    )
    db.add(audit)
    db.commit()

    logs = []
    logs.append(f"Modo ETL: {run_type}")
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
        artists_new, artists_skipped = EtlService.load_artists(db, artists_transformed, full_run=is_full_run)
        tracks_new, tracks_skipped, new_tracks_detail = EtlService.load_tracks(db, tracks_transformed, full_run=is_full_run)
        history_new, history_skipped, new_history_detail = EtlService.load_history(db, current_user.spotify_id, history_transformed)

        # ── Backfill solo en ETL full ─────────────────────────────────────────
        if is_full_run:
            logs.append("Enriqueciendo datos (ETL full)...")
            all_artist_ids = [r[0] for r in db.query(DimArtists.spotify_id).all()]
            enriched = EtlService.enrich_artists_from_spotify(db, all_artist_ids, access_token)
            if enriched:
                logs.append(f"Artistas enriquecidos con datos reales de Spotify: {enriched}")
            data_updated = EtlService.backfill_artist_data(db, spotify_token=access_token)
            if data_updated:
                logs.append(f"Artists enriched via Spotify: {data_updated} stubs updated")
            tracks_enriched = EtlService.backfill_track_images(db, spotify_token=access_token)
            if tracks_enriched:
                logs.append(f"Track images enriched via Spotify: {tracks_enriched} tracks updated")
            pop_enriched = EtlService.backfill_track_popularity(db, spotify_token=access_token)
            if pop_enriched:
                logs.append(f"Track popularity enriched via Spotify: {pop_enriched} tracks updated")
            genres_updated = EtlService.backfill_artist_genres(db)
            if genres_updated:
                logs.append(f"Genres enriched via Last.fm: {genres_updated} artists updated")
            stats_updated = EtlService.backfill_artist_stats(db)
            if stats_updated:
                logs.append(f"Stats actualizados: {stats_updated} artistas")
        else:
            logs.append("ETL incremental: backfill de Spotify y Last.fm omitido")

        logs.append(f"Cargado: {artists_new} artistas nuevos, {tracks_new} canciones nuevas, {history_new} historial nuevo")

        duration_ms = int((time.time() - t0) * 1000)
        audit.status = "success"
        audit.finished_at = datetime.utcnow()
        audit.duration_ms = duration_ms
        audit.is_full_run = is_full_run
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

        logger.info(f"ETL {run_type} completado en {duration_ms}ms")

        return {
            "status": "success",
            "run_type": run_type.lower(),
            "message": f"ETL {run_type.lower()} completado exitosamente",
            "logs": logs,
            "run_id": audit.audit_id,
            "summary": {
                "tracks_new": tracks_new,
                "tracks_updated": tracks_skipped,
                "history_new": history_new,
                "history_skipped": history_skipped,
                "new_tracks": new_tracks_detail,
                "new_history": new_history_detail[:30],
            },
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
            "run_type": run_type.lower(),
            "message": str(e),
            "logs": logs + [f"Error: {str(e)}"],
        }


@router.get("/status")
def get_etl_status(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Obteniendo estado ETL para {current_user.spotify_id}")

    tables = []

    last_sync = None
    last_successful_audit = db.query(EtlAudit).filter_by(
        spotify_user_id=current_user.spotify_id,
        status="success"
    ).order_by(desc(EtlAudit.finished_at)).first()
    if last_successful_audit and last_successful_audit.finished_at:
        last_sync = last_successful_audit.finished_at.isoformat() + "+00:00"

    artist_count = db.query(func.count(DimArtists.artist_id)).scalar() or 0
    tables.append({
        "table_name": "dim_artists",
        "record_count": artist_count,
        "last_sync": last_sync,
        "status": "loaded" if artist_count > 0 else "empty",
    })

    track_count = db.query(func.count(DimTracks.track_id)).scalar() or 0
    tables.append({
        "table_name": "dim_tracks",
        "record_count": track_count,
        "last_sync": last_sync,
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
        "last_sync": last_sync,
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
            "run_type": "full" if audit.is_full_run else "incremental",
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
            "run_type": "full" if audit.is_full_run else "incremental",
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
