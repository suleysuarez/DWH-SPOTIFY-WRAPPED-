"""
Rutas ETL: status, run.
Endpoints para monitorear y ejecutar el pipeline ETL.
"""

import logging
import json
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from app.core.database import get_db
from app.core.security import verify_jwt_token, extract_bearer_token
from app.models.models import (
    DimUsers, EtlAudit, DimArtists, DimTracks, FactListeningHistory
)
from app.schemas.schemas import EtlStatusResponse, EtlRunResponse, DwhTable, EtlRun
from app.services.etl_service import EtlService
from app.services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/etl", tags=["etl"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> DimUsers:
    """Dependency para verificar JWT y obtener usuario actual."""
    token = extract_bearer_token(authorization)
    payload = verify_jwt_token(token)
    user_id = int(payload["sub"])
    
    user = db.query(DimUsers).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    return user


@router.get("/status", response_model=EtlStatusResponse)
def get_etl_status(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Obtiene estado actual del DWH y historial de ejecuciones ETL.
    """
    logger.info(f"Obteniendo estado ETL para user_id={current_user.user_id}")
    
    # Estado de tablas
    tables = []
    
    # dim_artists
    artist_count = db.query(func.count(DimArtists.artist_id)).scalar() or 0
    last_artist_sync = db.query(func.max(DimArtists.created_at)).scalar()
    tables.append(DwhTable(
        table_name="dim_artists",
        record_count=artist_count,
        last_sync=last_artist_sync,
        status="loaded" if artist_count > 0 else "empty",
    ))
    
    # dim_tracks
    track_count = db.query(func.count(DimTracks.track_id)).scalar() or 0
    last_track_sync = db.query(func.max(DimTracks.created_at)).scalar()
    tables.append(DwhTable(
        table_name="dim_tracks",
        record_count=track_count,
        last_sync=last_track_sync,
        status="loaded" if track_count > 0 else "empty",
    ))
    
    # fact_listening_history
    history_count = db.query(
        func.count(FactListeningHistory.history_id)
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).scalar() or 0
    last_history_sync = db.query(
        func.max(FactListeningHistory.created_at)
    ).filter(
        FactListeningHistory.user_id == current_user.user_id
    ).scalar()
    tables.append(DwhTable(
        table_name="fact_listening_history",
        record_count=history_count,
        last_sync=last_history_sync,
        status="loaded" if history_count > 0 else "empty",
    ))
    
    # Historial de ejecuciones (últimas 5)
    recent_runs = db.query(EtlAudit).filter_by(
        user_id=current_user.user_id
    ).order_by(
        desc(EtlAudit.etl_id)
    ).limit(5).all()
    
    runs = [
        EtlRun(
            id=run.etl_id,
            started_at=run.started_at,
            duration_seconds=run.duration_ms // 1000 if run.duration_ms else None,
            records_extracted=run.records_extracted,
            records_loaded=run.records_loaded,
            status=run.status,
        )
        for run in recent_runs
    ]
    
    return EtlStatusResponse(tables=tables, recent_runs=runs)


@router.post("/run", response_model=EtlRunResponse)
def run_etl(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ejecuta el pipeline ETL completo.
    
    Fases:
    1. EXTRACT_USER, EXTRACT_ARTISTS, EXTRACT_TRACKS, EXTRACT_HISTORY
    2. TRANSFORM_USER, TRANSFORM_ARTISTS, TRANSFORM_TRACKS, TRANSFORM_HISTORY
    3. LOAD_USER, LOAD_ARTISTS, LOAD_TRACKS, LOAD_HISTORY
    
    Retorna: status, message, logs
    """
    logger.info(f"Iniciando ETL para user_id={current_user.user_id}")
    
    # Crear registro de auditoría
    etl_run = EtlAudit(
        user_id=current_user.user_id,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(etl_run)
    db.commit()
    
    logs = []
    try:
        # Renovar token si es necesario
        if current_user.token_expires_at and datetime.utcnow() > current_user.token_expires_at:
            logger.info("Token expirado, renovando...")
            token_response = SpotifyService.refresh_access_token(current_user.spotify_refresh_token)
            current_user.spotify_access_token = token_response["access_token"]
            db.commit()
            logs.append("Token renovado exitosamente")
        
        access_token = current_user.spotify_access_token
        
        # EXTRACT
        logs.append("Extrayendo datos de Spotify...")
        user_data = EtlService.extract_user(access_token)
        artists_data = EtlService.extract_top_artists(access_token)
        tracks_data = EtlService.extract_top_tracks(access_token)
        history_data, next_cursor = EtlService.extract_recently_played(
            access_token,
            cursor_next_ms=None,  # Primera ejecución
        )
        logs.append(f"Extraído: {len(artists_data)} artistas, {len(tracks_data)} canciones, {len(history_data)} historial")
        
        # TRANSFORM
        logs.append("Transformando datos...")
        user_transformed = EtlService.transform_user(user_data)
        artists_transformed = EtlService.transform_artists(artists_data)
        tracks_transformed = EtlService.transform_tracks(tracks_data)
        history_transformed = EtlService.transform_history(history_data)
        logs.append("Datos transformados exitosamente")
        
        # LOAD
        logs.append("Cargando datos en DWH...")
        user_id = EtlService.load_user(db, user_transformed, access_token, current_user.spotify_refresh_token)
        artists_loaded = EtlService.load_artists(db, artists_transformed)
        tracks_loaded = EtlService.load_tracks(db, tracks_transformed)
        history_loaded = EtlService.load_history(db, user_id, history_transformed)
        logs.append(f"Cargado: {artists_loaded} artistas, {tracks_loaded} canciones, {history_loaded} historial")
        
        # Actualizar auditoría
        etl_run.status = "success"
        etl_run.ended_at = datetime.utcnow()
        etl_run.duration_ms = int((etl_run.ended_at - etl_run.started_at).total_seconds() * 1000)
        etl_run.records_extracted = len(artists_data) + len(tracks_data) + len(history_data)
        etl_run.records_loaded = artists_loaded + tracks_loaded + history_loaded
        etl_run.cursor_next_ms = next_cursor
        etl_run.logs = json.dumps(logs)
        db.commit()
        
        logger.info(f"ETL completado exitosamente: {etl_run.records_loaded} registros cargados")
        
        return EtlRunResponse(
            status="success",
            message="ETL completado exitosamente",
            logs=logs,
        )
    
    except Exception as e:
        logger.error(f"Error en ETL: {e}", exc_info=True)
        
        etl_run.status = "error"
        etl_run.ended_at = datetime.utcnow()
        etl_run.duration_ms = int((etl_run.ended_at - etl_run.started_at).total_seconds() * 1000)
        etl_run.error_message = str(e)
        etl_run.logs = json.dumps(logs + [f"Error: {str(e)}"])
        db.commit()
        
        return EtlRunResponse(
            status="error",
            message=str(e),
            logs=logs + [f"Error: {str(e)}"],
        )
