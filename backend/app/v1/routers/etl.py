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
            # Verificar que el token existente siga siendo válido
            try:
                SpotifyClient.get_current_user(access_token)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tu sesión de Spotify expiró. Por favor cierra sesión y vuelve a iniciar."
                )

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
        history_new, history_skipped, new_history_detail, new_catalog_from_history = EtlService.load_history(db, current_user.spotify_id, history_transformed, spotify_token=access_token)
        new_tracks_detail.extend(new_catalog_from_history)
        tracks_new += len(new_catalog_from_history)

        # ── Rellenar nulls: corre siempre (son baratos, solo tocan registros con null) ──
        incomplete_artist_ids = [
            r[0] for r in db.query(DimArtists.spotify_id).filter(
                (DimArtists.followers_count == None) | (DimArtists.image_url == None)
            ).all()
        ]
        if incomplete_artist_ids:
            enriched = EtlService.enrich_artists_from_spotify(db, incomplete_artist_ids, access_token)
            if enriched:
                logs.append(f"Artistas incompletos enriquecidos: {enriched}")

        tracks_enriched = EtlService.backfill_track_images(db, spotify_token=access_token)
        if tracks_enriched:
            logs.append(f"Imágenes de tracks actualizadas: {tracks_enriched}")

        pop_enriched = EtlService.backfill_track_popularity(db, spotify_token=access_token)
        if pop_enriched:
            logs.append(f"Popularidad de tracks actualizada: {pop_enriched}")

        # ── Stats via Last.fm: corre siempre, solo toca artistas con null ──────
        stats_updated = EtlService.backfill_artist_stats(db)
        if stats_updated:
            logs.append(f"Stats actualizados via Last.fm: {stats_updated}")

        # ── Backfill pesado: solo en ETL full (refresh completo de Spotify) ──
        if is_full_run:
            logs.append("Enriqueciendo datos completos (ETL full)...")
            all_artist_ids = [r[0] for r in db.query(DimArtists.spotify_id).all()]
            enriched_all = EtlService.enrich_artists_from_spotify(db, all_artist_ids, access_token)
            if enriched_all:
                logs.append(f"Todos los artistas refrescados: {enriched_all}")
            data_updated = EtlService.backfill_artist_data(db, spotify_token=access_token)
            if data_updated:
                logs.append(f"Stubs de artistas reparados: {data_updated}")
            genres_updated = EtlService.backfill_artist_genres(db)
            if genres_updated:
                logs.append(f"Géneros actualizados via Last.fm: {genres_updated}")
        else:
            logs.append("ETL incremental: refresh completo de Spotify omitido")

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
                "new_tracks": [t for t in new_tracks_detail if t.get("name")][:30],
                "new_history": [h for h in new_history_detail if h.get("track_name")][:30],
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


@router.post("/backfill-tracks")
def backfill_tracks(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Rellena popularity y album_image_url de tracks con datos nulos via /v1/search.
    """
    from sqlalchemy import or_
    stubs = (
        db.query(DimTracks, DimArtists.name.label("artist_name"))
        .outerjoin(DimArtists, DimTracks.artist_id == DimArtists.artist_id)
        .filter(or_(
            DimTracks.popularity.is_(None),
            DimTracks.album_image_url.is_(None),
        ))
        .all()
    )

    if not stubs:
        return {"message": "No hay tracks con datos faltantes", "updated": 0}

    access_token = current_user.spotify_access_token
    if current_user.spotify_refresh_token:
        try:
            new_tokens = SpotifyClient.refresh_access_token(
                current_user.spotify_refresh_token,
                settings.SPOTIFY_CLIENT_ID,
                settings.SPOTIFY_CLIENT_SECRET,
            )
            access_token = new_tokens["access_token"]
        except Exception:
            pass

    search_token = access_token
    if settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
        try:
            search_token = SpotifyClient.get_client_credentials_token(
                settings.SPOTIFY_CLIENT_ID,
                settings.SPOTIFY_CLIENT_SECRET,
            )
        except Exception:
            pass

    from concurrent.futures import ThreadPoolExecutor, as_completed as _ac

    def _search(row) -> tuple:
        track = row.DimTracks
        artist_name = row.artist_name or ""
        try:
            result = SpotifyClient.search_track(search_token, track.name, artist_name)
            return track.track_id, result
        except Exception:
            return track.track_id, None

    results_map: dict = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futs = {executor.submit(_search, row): row for row in stubs}
        for fut in _ac(futs):
            tid, result = fut.result()
            if result:
                results_map[tid] = result

    updated = 0
    for row in stubs:
        track = row.DimTracks
        sp = results_map.get(track.track_id)
        if not sp:
            continue
        album = sp.get("album") or {}
        images = album.get("images") or []
        pop = sp.get("popularity")
        if pop is not None and track.popularity is None:
            track.popularity = pop
        if images and track.album_image_url is None:
            track.album_image_url = images[0]["url"]
        updated += 1

    db.commit()
    logger.info(f"backfill-tracks: {updated}/{len(stubs)} tracks actualizados")

    return {
        "message": f"{updated}/{len(stubs)} tracks actualizados",
        "updated": updated,
        "total_stubs": len(stubs),
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


@router.post("/backfill-artists")
def backfill_artists(
    current_user: DimUsers = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fuerza el enriquecimiento de todos los artistas con datos nulos (image_url, popularity, followers_count).
    Devuelve un reporte detallado por artista.
    """
    from sqlalchemy import or_
    stubs = db.query(DimArtists).filter(
        or_(
            DimArtists.image_url.is_(None),
            DimArtists.popularity.is_(None),
            DimArtists.followers_count.is_(None),
        )
    ).all()

    if not stubs:
        return {"message": "No hay artistas con datos faltantes", "updated": 0, "results": []}

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
        except Exception as e:
            logger.warning(f"Token refresh falló en backfill: {e}")

    api_errors: list = []
    cc_configured = bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET)

    # Obtener token de búsqueda (CC preferido, fallback user token)
    search_token = access_token
    if cc_configured:
        try:
            search_token = SpotifyClient.get_client_credentials_token(
                settings.SPOTIFY_CLIENT_ID,
                settings.SPOTIFY_CLIENT_SECRET,
            )
        except Exception as e:
            api_errors.append(f"CC token falló, usando user token: {e}")

    # 1. Intentar endpoint individual /v1/artists/{id} (más preciso que search)
    # 2. Fallback a /v1/search por nombre si el individual también da 403
    from concurrent.futures import ThreadPoolExecutor, as_completed as futures_done

    spotify_map: dict = {}
    id_hits = 0
    search_hits = 0

    def _fetch(artist) -> tuple:
        # Intento 1: endpoint individual por ID
        try:
            result = SpotifyClient.get_artist(search_token, artist.spotify_id)
            if result:
                return artist.spotify_id, result, "id"
        except Exception:
            pass
        # Intento 2: search por nombre
        try:
            result = SpotifyClient.search_artist(search_token, artist.name)
            return artist.spotify_id, result, "search"
        except Exception:
            return artist.spotify_id, None, "failed"

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futs = {executor.submit(_fetch, a): a for a in stubs}
            for fut in futures_done(futs):
                sid, result, method = fut.result()
                if result:
                    spotify_map[sid] = result
                    if method == "id":
                        id_hits += 1
                    else:
                        search_hits += 1
    except Exception as e:
        api_errors.append(f"Error en fetch concurrente: {type(e).__name__}: {e}")

    logger.info(f"backfill-artists: {id_hits} por ID, {search_hits} por search, {len(spotify_map)}/{len(stubs)} total")

    results = []
    updated_count = 0

    for artist in stubs:
        sp = spotify_map.get(artist.spotify_id)
        entry = {
            "artist_id": artist.artist_id,
            "name": artist.name,
            "spotify_id": artist.spotify_id,
            "spotify_found": sp is not None,
            "before": {
                "popularity": artist.popularity,
                "followers_count": artist.followers_count,
                "has_image": artist.image_url is not None,
            },
        }

        if sp:
            images = sp.get("images") or []
            new_pop = sp.get("popularity")
            new_followers = (sp.get("followers") or {}).get("total")
            new_image = images[0]["url"] if images else None
            new_genres = sp.get("genres") or []

            if new_pop is not None:
                artist.popularity = new_pop
            if new_followers is not None:
                artist.followers_count = new_followers
            if new_image:
                artist.image_url = new_image
            if new_genres and (not artist.genres or artist.genres == [""]):
                from sqlalchemy.orm.attributes import flag_modified
                artist.genres = new_genres
                flag_modified(artist, "genres")

            entry["after"] = {
                "popularity": artist.popularity,
                "followers_count": artist.followers_count,
                "has_image": artist.image_url is not None,
            }
            updated_count += 1
        else:
            entry["after"] = entry["before"]
            entry["error"] = "Spotify no devolvió datos para este ID"

        results.append(entry)

    db.commit()

    not_found = [r for r in results if not r["spotify_found"]]
    logger.info(f"backfill-artists completado: {updated_count}/{len(stubs)} actualizados, {len(not_found)} no encontrados en Spotify")

    return {
        "message": f"{updated_count}/{len(stubs)} artistas actualizados",
        "updated": updated_count,
        "api_errors": api_errors,
        "cc_configured": cc_configured,
        "fetch_stats": {"by_id": id_hits, "by_search": search_hits},
        "not_found_in_spotify": [r["name"] for r in not_found],
        "results": results,
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
