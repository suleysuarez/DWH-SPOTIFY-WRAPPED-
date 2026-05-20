"""
filename: etl_service.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Orquestador del pipeline ETL (versión activa). Clase EtlService con métodos
             agrupados en Extract (Spotify API), Transform (normalización) y Load (upsert DWH).
             Incluye Circuit Breaker para Last.fm y Spotify.
"""

import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.models import DimUsers, DimArtists, DimTracks, FactListeningHistory
from app.v1.services.spotify_client import SpotifyClient
from app.core.config import settings
from app.core.circuit_breaker import lastfm_breaker, CircuitBreakerError

logger = logging.getLogger(__name__)


class EtlService:
    """Orquestador del pipeline ETL."""

    # ============ HELPERS ============

    @staticmethod
    def fetch_lastfm_genres(artist_name: str) -> List[str]:
        """
        Obtiene los géneros/tags de un artista desde la API de Last.fm.
        Protegido por Circuit Breaker.
        """
        if not settings.LASTFM_API_KEY:
            logger.warning("LASTFM_API_KEY no configurado, saltando géneros")
            return []
        try:
            def _call():
                return requests.get(
                    "https://ws.audioscrobbler.com/2.0/",
                    params={
                        "method": "artist.getTopTags",
                        "artist": artist_name,
                        "api_key": settings.LASTFM_API_KEY,
                        "format": "json",
                        "autocorrect": 1,
                    },
                    timeout=2,
                )
            response = lastfm_breaker.call(_call)
            data = response.json()
            logger.info(f"[LASTFM] {artist_name} → raw: {data}")
            tags = data.get("toptags", {}).get("tag", [])
            genres = [t["name"].lower() for t in tags[:5] if t.get("name")]
            logger.info(f"[LASTFM] {artist_name} → genres: {genres}")
            return genres
        except CircuitBreakerError as e:
            logger.warning(f"[CircuitBreaker] Last.fm no disponible para '{artist_name}': {e}")
            return []
        except Exception as e:
            logger.warning(f"Last.fm fallo para '{artist_name}': {e}")
            return []

    @staticmethod
    def fetch_lastfm_listeners(artist_name: str) -> Optional[int]:
        """
        Obtiene el número de listeners de un artista desde Last.fm.
        Protegido por Circuit Breaker.
        """
        if not settings.LASTFM_API_KEY:
            return None
        try:
            def _call():
                return requests.get(
                    "https://ws.audioscrobbler.com/2.0/",
                    params={
                        "method": "artist.getInfo",
                        "artist": artist_name,
                        "api_key": settings.LASTFM_API_KEY,
                        "format": "json",
                        "autocorrect": 1,
                    },
                    timeout=2,
                )
            response = lastfm_breaker.call(_call)
            data = response.json()
            listeners = data.get("artist", {}).get("stats", {}).get("listeners")
            return int(listeners) if listeners else None
        except CircuitBreakerError as e:
            logger.warning(f"[CircuitBreaker] Last.fm no disponible para listeners '{artist_name}': {e}")
            return None
        except Exception as e:
            logger.warning(f"Last.fm listeners fallo para '{artist_name}': {e}")
            return None

    @staticmethod
    def fetch_lastfm_playcount(artist_name: str) -> Optional[int]:
        """
        Obtiene el playcount total de un artista desde Last.fm.
        Protegido por Circuit Breaker.
        """
        if not settings.LASTFM_API_KEY:
            return None
        try:
            def _call():
                return requests.get(
                    "https://ws.audioscrobbler.com/2.0/",
                    params={
                        "method": "artist.getInfo",
                        "artist": artist_name,
                        "api_key": settings.LASTFM_API_KEY,
                        "format": "json",
                        "autocorrect": 1,
                    },
                    timeout=2,
                )
            response = lastfm_breaker.call(_call)
            data = response.json()
            playcount = data.get("artist", {}).get("stats", {}).get("playcount")
            return int(playcount) if playcount else None
        except CircuitBreakerError as e:
            logger.warning(f"[CircuitBreaker] Last.fm no disponible para playcount '{artist_name}': {e}")
            return None
        except Exception as e:
            logger.warning(f"Last.fm playcount fallo para '{artist_name}': {e}")
            return None

    @staticmethod
    def fetch_lastfm_track_playcount(track_name: str, artist_name: str) -> Optional[int]:
        """
        Obtiene el playcount de una canción desde Last.fm.
        Protegido por Circuit Breaker.
        """
        if not settings.LASTFM_API_KEY:
            return None
        try:
            def _call():
                return requests.get(
                    "https://ws.audioscrobbler.com/2.0/",
                    params={
                        "method": "track.getInfo",
                        "track": track_name,
                        "artist": artist_name,
                        "api_key": settings.LASTFM_API_KEY,
                        "format": "json",
                        "autocorrect": 1,
                    },
                    timeout=2,
                )
            response = lastfm_breaker.call(_call)
            data = response.json()
            playcount = data.get("track", {}).get("playcount")
            return int(playcount) if playcount else None
        except CircuitBreakerError as e:
            logger.warning(f"[CircuitBreaker] Last.fm no disponible para track '{track_name}': {e}")
            return None
        except Exception as e:
            logger.warning(f"Last.fm track playcount fallo para '{track_name}': {e}")
            return None

    # ============ EXTRACT ============

    @staticmethod
    def extract_user(token: str) -> Dict[str, Any]:
        logger.info("Extrayendo datos del usuario...")
        user = SpotifyClient.get_current_user(token)
        logger.info(f"Usuario extraido: {user['id']}")
        return user

    @staticmethod
    def extract_top_artists(token: str) -> List[Dict[str, Any]]:
        logger.info("Extrayendo top artistas...")
        response = SpotifyClient.get_top_artists(token, limit=50)
        artists = response.get("items", [])
        logger.info(f"Artistas extraidos: {len(artists)}")
        if artists:
            a = artists[0]
            logger.info(f"[DEBUG] Primer artista crudo — name={a.get('name')} popularity={a.get('popularity')} followers={a.get('followers')} genres={a.get('genres')}")
        return artists

    @staticmethod
    def extract_top_tracks(token: str) -> List[Dict[str, Any]]:
        logger.info("Extrayendo top canciones...")
        response = SpotifyClient.get_top_tracks(token, limit=50)
        tracks = response.get("items", [])
        logger.info(f"Canciones extraidas: {len(tracks)}")
        return tracks

    @staticmethod
    def extract_recently_played(token: str, after: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        logger.info("Extrayendo historial de reproduccion...")
        response = SpotifyClient.get_recently_played(token, limit=50, after=after)
        if not response:
            logger.warning("Respuesta vacia de recently-played")
            return [], None
        items = response.get("items", [])
        next_cursor = (response.get("cursors") or {}).get("after")
        logger.info(f"Historial extraido: {len(items)} items, next_cursor: {next_cursor}")
        return items, next_cursor

    # ============ TRANSFORM ============

    @staticmethod
    def transform_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Transformando datos del usuario...")
        images = user_data.get("images", [])
        transformed = {
            "spotify_id": user_data["id"],
            "display_name": user_data.get("display_name"),
            "email": user_data.get("email"),
            "country": user_data.get("country"),
            "followers": user_data.get("followers", {}).get("total", 0),
            "product": user_data.get("product", "free"),
            "image_url": images[0]["url"] if images else None,
        }
        logger.info(f"Usuario transformado: {transformed['spotify_id']}")
        return transformed

    @staticmethod
    def transform_artists(artists_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"Transformando {len(artists_data)} artistas...")
        transformed = []
        for artist in artists_data:
            images = artist.get("images", [])
            image_url = images[0]["url"] if images else None
            transformed.append({
                "spotify_id": artist["id"],
                "name": artist["name"],
                "popularity": artist.get("popularity"),
                "followers_count": artist.get("followers", {}).get("total"),
                "genres": artist.get("genres", []),
                "image_url": image_url,
            })
        logger.info(f"Artistas transformados: {len(transformed)}")
        return transformed

    @staticmethod
    def transform_tracks(tracks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"Transformando {len(tracks_data)} canciones...")
        transformed = []
        for track in tracks_data:
            album = track.get("album", {})
            transformed.append({
                "spotify_id": track["id"],
                "name": track["name"],
                "spotify_artist_id": track["artists"][0]["id"] if track.get("artists") else None,
                "artist_name": track["artists"][0]["name"] if track.get("artists") else None,
                "album_name": album.get("name"),
                "duration_ms": track.get("duration_ms"),
                "popularity": track.get("popularity"),
                "explicit": track.get("explicit", False),
                "album_image_url": album.get("images", [{}])[0].get("url") if album.get("images") else None,
            })
        logger.info(f"Canciones transformadas: {len(transformed)}")
        return transformed

    @staticmethod
    def transform_history(history_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"Transformando {len(history_data)} registros de historial...")
        transformed = []
        for item in history_data:
            track = item.get("track", {})
            album = track.get("album", {})
            artists = track.get("artists", [{}])
            context = item.get("context", {})
            played_at_str = item.get("played_at", "").replace("Z", "+00:00")
            played_at = datetime.fromisoformat(played_at_str)
            transformed.append({
                "spotify_track_id": track.get("id"),
                "spotify_artist_id": artists[0].get("id") if artists else None,
                "track_name": track.get("name"),
                "artist_name": artists[0].get("name") if artists else None,
                "album_name": album.get("name"),
                "album_image_url": album.get("images", [{}])[0].get("url") if album.get("images") else None,
                "duration_ms": track.get("duration_ms"),
                "popularity": track.get("popularity"),
                "explicit": track.get("explicit", False),
                "played_at": played_at,
                "hour_of_day": played_at.hour,
                "day_of_week": played_at.strftime("%A"),
                "context_type": context.get("type") if context else "unknown",
            })
        logger.info(f"Historial transformado: {len(transformed)}")
        return transformed

    @staticmethod
    def backfill_artist_genres(db: Session) -> int:
        """
        Enriquece con Last.fm todos los artistas del DWH que aún tienen genres vacío.
        """
        if not settings.LASTFM_API_KEY:
            return 0
        from sqlalchemy import func as sa_func
        empty_artists = db.query(DimArtists).filter(
            sa_func.coalesce(sa_func.cardinality(DimArtists.genres), 0) == 0
        ).all()
        results: Dict[str, List[str]] = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_name = {
                executor.submit(EtlService.fetch_lastfm_genres, a.name): a.name
                for a in empty_artists
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception:
                    results[name] = []

        updated = 0
        for artist in empty_artists:
            genres = results.get(artist.name, [])
            artist.genres = genres if genres else [""]
            flag_modified(artist, "genres")
            if genres:
                updated += 1
        if empty_artists:
            db.commit()
        logger.info(f"[LASTFM] Backfill géneros: {updated}/{len(empty_artists)} artistas actualizados")
        return updated

    @staticmethod
    def backfill_artist_stats(db: Session) -> int:
        """
        Llena popularity y followers_count para todos los artistas con NULL.
        """
        from sqlalchemy import func as sa_func
        artists = db.query(DimArtists).filter(
            (DimArtists.popularity.is_(None)) | (DimArtists.followers_count.is_(None))
        ).all()
        if not artists:
            return 0

        lastfm_results: Dict[str, Dict[str, Optional[int]]] = {}
        if settings.LASTFM_API_KEY:
            def fetch_stats(name: str) -> Dict[str, Optional[int]]:
                return {
                    "listeners": EtlService.fetch_lastfm_listeners(name),
                    "playcount": EtlService.fetch_lastfm_playcount(name),
                }
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_name = {
                    executor.submit(fetch_stats, a.name): a.name
                    for a in artists
                }
                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        lastfm_results[name] = future.result()
                    except Exception:
                        lastfm_results[name] = {"listeners": None, "playcount": None}

        play_counts = dict(
            db.query(DimArtists.artist_id, sa_func.count(FactListeningHistory.id))
            .join(FactListeningHistory, FactListeningHistory.artist_id == DimArtists.artist_id)
            .group_by(DimArtists.artist_id)
            .all()
        )
        max_plays = max(play_counts.values(), default=1)

        updated = 0
        for artist in artists:
            stats = lastfm_results.get(artist.name, {})
            plays = play_counts.get(artist.artist_id, 1)

            if artist.popularity is None:
                artist.popularity = max(1, round(plays * 100 / max_plays))

            if artist.followers_count is None:
                estimated = max(1, plays * 500)
                lastfm_listeners = stats.get("listeners") or 0
                artist.followers_count = max(estimated, lastfm_listeners)

            updated += 1

        if artists:
            db.commit()
        logger.info(f"[LASTFM] Backfill stats: {updated}/{len(artists)} artistas actualizados")
        return updated

    # ============ LOAD ============

    @staticmethod
    def load_user(db: Session, user_data: Dict[str, Any], access_token: str, refresh_token: Optional[str]) -> str:
        logger.info(f"Cargando usuario {user_data['spotify_id']}...")
        user = db.query(DimUsers).filter_by(spotify_id=user_data["spotify_id"]).first()
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            user.spotify_access_token = access_token
            if refresh_token:
                user.spotify_refresh_token = refresh_token
        else:
            user = DimUsers(
                **user_data,
                spotify_access_token=access_token,
                spotify_refresh_token=refresh_token,
            )
            db.add(user)
        db.commit()
        logger.info(f"Usuario cargado: {user.spotify_id}")
        return user.spotify_id

    @staticmethod
    def load_artists(db: Session, artists_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        logger.info(f"Cargando {len(artists_data)} artistas...")
        new_count = 0
        updated_count = 0
        for artist in artists_data:
            existing = db.query(DimArtists).filter_by(spotify_id=artist["spotify_id"]).first()
            incoming_genres = artist.get("genres") or []
            if not incoming_genres:
                fetched = EtlService.fetch_lastfm_genres(artist["name"])
                incoming_genres = fetched if fetched else [""]

            if not existing:
                artist["genres"] = incoming_genres
                db.add(DimArtists(**artist))
                new_count += 1
            else:
                existing.genres = incoming_genres if incoming_genres else (existing.genres or [""])
                flag_modified(existing, "genres")
                if artist.get("popularity") is not None:
                    existing.popularity = artist["popularity"]
                if artist.get("followers_count") is not None:
                    existing.followers_count = artist["followers_count"]
                if existing.followers_count is None:
                    try:
                        listeners = EtlService.fetch_lastfm_listeners(existing.name)
                        if listeners:
                            existing.followers_count = listeners
                    except Exception as e:
                        logger.warning(f"Error listeners para '{existing.name}': {e}")
                if existing.popularity is None:
                    try:
                        playcount = EtlService.fetch_lastfm_playcount(existing.name)
                        if playcount:
                            existing.popularity = playcount
                    except Exception as e:
                        logger.warning(f"Error playcount para '{existing.name}': {e}")
                if artist.get("image_url"):
                    existing.image_url = artist["image_url"]
                updated_count += 1
        db.commit()
        logger.info(f"Artistas cargados: {new_count} nuevos, {updated_count} actualizados")
        return new_count, updated_count

    @staticmethod
    def load_tracks(db: Session, tracks_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        logger.info(f"Cargando {len(tracks_data)} canciones...")
        new_count = 0
        updated_count = 0
        for track in tracks_data:
            existing = db.query(DimTracks).filter_by(spotify_id=track["spotify_id"]).first()
            if not existing:
                artist = db.query(DimArtists).filter_by(
                    spotify_id=track["spotify_artist_id"]
                ).first()
                if not artist:
                    logger.warning(f"Artista no encontrado para track {track['spotify_id']}, creando artista basico...")
                    artist = DimArtists(
                        spotify_id=track["spotify_artist_id"],
                        name=track.get("artist_name", "Desconocido"),
                        genres=[],
                    )
                    db.add(artist)
                    db.flush()
                track_data = {k: v for k, v in track.items() if k not in ("spotify_artist_id", "artist_name")}
                track_data["artist_id"] = artist.artist_id
                db.add(DimTracks(**track_data))
                new_count += 1
            else:
                if track.get("popularity") is not None:
                    existing.popularity = track["popularity"]
                existing.explicit = track.get("explicit") if track.get("explicit") is not None else existing.explicit
                if track.get("album_image_url"):
                    existing.album_image_url = track["album_image_url"]
                if existing.artist_id is None:
                    artist = db.query(DimArtists).filter_by(
                        spotify_id=track["spotify_artist_id"]
                    ).first()
                    if artist:
                        existing.artist_id = artist.artist_id
                        logger.info(f"Reparado artist_id para track {track['spotify_id']}")
                if existing.popularity is None:
                    artist_name = None
                    if existing.artist_id:
                        artist = db.query(DimArtists).filter_by(artist_id=existing.artist_id).first()
                        artist_name = artist.name if artist else None
                    if artist_name:
                        try:
                            playcount = EtlService.fetch_lastfm_track_playcount(existing.name, artist_name)
                            if playcount:
                                existing.popularity = playcount
                        except Exception as e:
                            logger.warning(f"Error playcount track '{existing.name}': {e}")
                updated_count += 1
        db.commit()
        logger.info(f"Canciones cargadas: {new_count} nuevas, {updated_count} actualizadas")
        return new_count, updated_count

    @staticmethod
    def load_history(db: Session, spotify_user_id: str, history_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        logger.info(f"Cargando {len(history_data)} registros de historial...")
        new_count = 0
        skipped_count = 0
        user = db.query(DimUsers).filter_by(spotify_id=spotify_user_id).first()
        if not user:
            logger.error(f"Usuario no encontrado: {spotify_user_id}")
            return 0, 0

        for item in history_data:
            track = db.query(DimTracks).filter_by(
                spotify_id=item["spotify_track_id"]
            ).first()

            if track and track.popularity is None and item.get("popularity") is not None:
                track.popularity = item["popularity"]

            if not track:
                spotify_artist_id = item.get("spotify_artist_id")
                if not item.get("track_name") or not spotify_artist_id:
                    logger.warning(f"Datos insuficientes para track {item['spotify_track_id']}, saltando...")
                    skipped_count += 1
                    continue

                try:
                    with db.begin_nested():
                        artist = db.query(DimArtists).filter_by(spotify_id=spotify_artist_id).first()
                        if not artist:
                            fetched = EtlService.fetch_lastfm_genres(item.get("artist_name", ""))
                            artist = DimArtists(
                                spotify_id=spotify_artist_id,
                                name=item.get("artist_name", "Desconocido"),
                                genres=fetched if fetched else [""],
                            )
                            db.add(artist)
                            db.flush()

                        track = DimTracks(
                            spotify_id=item["spotify_track_id"],
                            name=item["track_name"],
                            artist_id=artist.artist_id,
                            album_name=item.get("album_name"),
                            album_image_url=item.get("album_image_url"),
                            duration_ms=item.get("duration_ms"),
                            popularity=item.get("popularity"),
                            explicit=item.get("explicit", False),
                        )
                        db.add(track)
                        db.flush()
                        logger.info(f"Track creado desde historial: {track.name}")
                except Exception as e:
                    logger.warning(f"No se pudo crear track {item['spotify_track_id']}: {e}")
                    skipped_count += 1
                    continue

            artist_id = track.artist_id
            if artist_id is None:
                spotify_artist_id = item.get("spotify_artist_id")
                if spotify_artist_id:
                    artist = db.query(DimArtists).filter_by(spotify_id=spotify_artist_id).first()
                    if artist:
                        artist_id = artist.artist_id
                        track.artist_id = artist_id
                        db.flush()

            if artist_id is None:
                logger.warning(f"No se pudo obtener artist_id para track {item['spotify_track_id']}, saltando...")
                skipped_count += 1
                continue

            stmt = pg_insert(FactListeningHistory).values(
                user_id=user.user_id,
                track_id=track.track_id,
                artist_id=artist_id,
                played_at=item["played_at"],
                hour_of_day=item.get("hour_of_day"),
                day_of_week=item.get("day_of_week"),
                context_type=item.get("context_type"),
            ).on_conflict_do_nothing(
                index_elements=["user_id", "played_at"]
            )
            result = db.execute(stmt)
            if result.rowcount > 0:
                new_count += 1
            else:
                skipped_count += 1

        db.commit()
        logger.info(f"Historial cargado: {new_count} nuevos, {skipped_count} saltados")
        return new_count, skipped_count