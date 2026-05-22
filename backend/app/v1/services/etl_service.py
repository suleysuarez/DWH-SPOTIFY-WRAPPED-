"""
filename: etl_service.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Orquestador del pipeline ETL (versión activa). Clase EtlService con métodos
             agrupados en Extract (Spotify API), Transform (normalización) y Load (upsert DWH).
"""

import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.models import DimUsers, DimArtists, DimTracks, FactListeningHistory
from app.v1.services.spotify_client import SpotifyClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class EtlService:
    """Orquestador del pipeline ETL."""

    # ============ HELPERS ============

    @staticmethod
    def fetch_lastfm_genres(artist_name: str) -> List[str]:
        """
        Obtiene los géneros/tags de un artista desde la API de Last.fm.

        Args:
            artist_name (str): Nombre del artista a consultar.

        Returns:
            List[str]: Lista de géneros (top 5 tags), vacía si no hay API key o falla la llamada.
        """
        if not settings.LASTFM_API_KEY:
            logger.warning("LASTFM_API_KEY no configurado, saltando géneros")
            return []
        try:
            response = requests.get(
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
            data = response.json()
            logger.info(f"[LASTFM] {artist_name} → raw: {data}")
            tags = data.get("toptags", {}).get("tag", [])
            genres = [t["name"].lower() for t in tags[:5] if t.get("name")]
            logger.info(f"[LASTFM] {artist_name} → genres: {genres}")
            return genres
        except Exception as e:
            logger.warning(f"Last.fm fallo para '{artist_name}': {e}")
            return []

    # ============ EXTRACT ============

    @staticmethod
    def extract_user(token: str) -> Dict[str, Any]:
        """
        Obtiene los datos del usuario autenticado desde la Spotify API.

        Args:
            token (str): Access token válido de Spotify.

        Returns:
            Dict[str, Any]: Datos del usuario (id, display_name, email, country, followers, product, images).
        """
        logger.info("Extrayendo datos del usuario...")
        user = SpotifyClient.get_current_user(token)
        logger.info(f"Usuario extraido: {user['id']}")
        return user

    @staticmethod
    def extract_top_artists(token: str) -> List[Dict[str, Any]]:
        """
        Obtiene los top 50 artistas del usuario desde la Spotify API.

        Args:
            token (str): Access token válido de Spotify.

        Returns:
            List[Dict[str, Any]]: Lista de artistas con id, name, popularity, followers y genres.
        """
        logger.info("Extrayendo top artistas...")
        response = SpotifyClient.get_top_artists(token, limit=50)
        artists = response.get("items", [])
        logger.info(f"Artistas extraidos: {len(artists)}")
        return artists

    @staticmethod
    def extract_top_tracks(token: str) -> List[Dict[str, Any]]:
        """
        Obtiene las top 50 canciones del usuario desde la Spotify API.

        Args:
            token (str): Access token válido de Spotify.

        Returns:
            List[Dict[str, Any]]: Lista de canciones con id, name, artists, album, duration_ms y popularity.
        """
        logger.info("Extrayendo top canciones...")
        response = SpotifyClient.get_top_tracks(token, limit=50)
        tracks = response.get("items", [])
        logger.info(f"Canciones extraidas: {len(tracks)}")
        return tracks

    @staticmethod
    def extract_recently_played(token: str, after: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Obtiene el historial de reproducción reciente con soporte de cursor para paginación incremental.

        Args:
            token (str): Access token válido de Spotify.
            after (Optional[str]): Timestamp en milisegundos (cursor) para traer solo reproducciones posteriores a ese punto.

        Returns:
            Tuple[List[Dict[str, Any]], Optional[str]]: Tupla (items, next_cursor) donde items es la lista de
            reproducciones y next_cursor es el cursor para la siguiente página o None si no hay más.
        """
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
        """
        Normaliza los datos crudos del usuario de Spotify al esquema del DWH.

        Args:
            user_data (Dict[str, Any]): Respuesta cruda de GET /me de la Spotify API.

        Returns:
            Dict[str, Any]: Dict con claves spotify_id, display_name, email, country,
            followers, product e image_url listo para upsert en dim_users.
        """
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
        """
        Normaliza la lista de artistas de Spotify al esquema del DWH.

        Args:
            artists_data (List[Dict[str, Any]]): Lista de artistas crudos de GET /me/top/artists.

        Returns:
            List[Dict[str, Any]]: Lista de dicts con spotify_id, name, popularity,
            followers_count, genres e image_url listos para upsert en dim_artists.
        """
        logger.info(f"Transformando {len(artists_data)} artistas...")
        transformed = []
        for artist in artists_data:
            # Tomar la imagen de mayor resolucion disponible
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
        """
        Normaliza la lista de canciones de Spotify al esquema del DWH.

        Args:
            tracks_data (List[Dict[str, Any]]): Lista de canciones crudas de GET /me/top/tracks.

        Returns:
            List[Dict[str, Any]]: Lista de dicts con spotify_id, name, spotify_artist_id,
            artist_name, album_name, duration_ms, popularity, explicit y album_image_url
            listos para upsert en dim_tracks.
        """
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
        """
        Normaliza los items del historial de reproducción al esquema del DWH.

        Incluye todos los campos del objeto track para poder crear el registro en
        dim_tracks si la canción no existe aún (p.ej. canciones fuera del top 50).

        Args:
            history_data (List[Dict[str, Any]]): Items crudos de GET /me/player/recently-played.

        Returns:
            List[Dict[str, Any]]: Lista de dicts con spotify_track_id, spotify_artist_id,
            track_name, artist_name, album_name, album_image_url, duration_ms, popularity,
            explicit, played_at (datetime UTC), hour_of_day, day_of_week y context_type.
        """
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

        Returns:
            int: Cantidad de artistas actualizados.
        """
        if not settings.LASTFM_API_KEY:
            return 0
        from sqlalchemy import func as sa_func
        empty_artists = db.query(DimArtists).filter(
            sa_func.coalesce(sa_func.cardinality(DimArtists.genres), 0) == 0
        ).all()
        # Llamadas a Last.fm en paralelo (máx 10 workers) para no bloquear el ETL.
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
            # [''] como sentinel: cardinality=1 → el backfill no lo reintenta;
            # el endpoint filtra strings vacíos.
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
        Actualiza popularity y followers_count de artistas con datos nulos usando Last.fm listeners.
        Solo se llama en ETL full para no saturar la API de Last.fm en cada ejecución.
        """
        import math
        from sqlalchemy import func as sa_func, or_
        if not settings.LASTFM_API_KEY:
            return 0

        stubs = db.query(DimArtists).filter(
            or_(
                DimArtists.popularity.is_(None),
                DimArtists.followers_count.is_(None),
            )
        ).all()
        if not stubs:
            return 0

        listeners_map: Dict[int, Optional[int]] = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            fut_map = {executor.submit(EtlService.fetch_lastfm_listeners, a.name): a for a in stubs}
            for fut in as_completed(fut_map):
                artist = fut_map[fut]
                try:
                    listeners_map[artist.artist_id] = fut.result()
                except Exception:
                    listeners_map[artist.artist_id] = None

        play_counts = dict(
            db.query(DimArtists.artist_id, sa_func.count(FactListeningHistory.id))
            .join(FactListeningHistory, FactListeningHistory.artist_id == DimArtists.artist_id)
            .group_by(DimArtists.artist_id)
            .all()
        )
        max_plays = max(play_counts.values(), default=1)
        LOG_MAX_LISTENERS = math.log1p(10_000_000)

        updated = 0
        for artist in stubs:
            listeners = listeners_map.get(artist.artist_id)
            plays = play_counts.get(artist.artist_id, 1)
            changed = False

            if artist.followers_count is None:
                artist.followers_count = listeners or max(1, plays * 500)
                changed = True

            if artist.popularity is None:
                if listeners:
                    artist.popularity = min(100, max(10, round(math.log1p(listeners) * 100 / LOG_MAX_LISTENERS)))
                else:
                    artist.popularity = max(10, round(math.log1p(plays) * 100 / math.log1p(max_plays)))
                changed = True

            if changed:
                updated += 1

        if stubs:
            db.commit()
        logger.info(f"[LASTFM] backfill_artist_stats: {updated}/{len(stubs)} artistas actualizados")
        return updated

    @staticmethod
    def backfill_artist_data(db: Session, spotify_token: Optional[str] = None) -> int:
        """
        Enriquece todos los artistas stub con datos reales de Spotify.

        Un artista es stub si le falta image_url, popularity o followers_count.
        image_url IS NULL es el indicador más confiable: los top-50 de Spotify
        siempre traen imagen; los creados desde historial/tracks nunca la tienen.

        Fuentes por prioridad:
          1. Spotify GET /v1/artists?ids=...  (popularity, followers, image, genres)
          2. Last.fm                          (fallback géneros y listeners)
          3. play_count proporcional          (último recurso popularity/followers)
        """
        import math
        from sqlalchemy import func as sa_func, or_

        stubs = db.query(DimArtists).filter(
            or_(
                DimArtists.image_url.is_(None),
                DimArtists.popularity.is_(None),
                DimArtists.followers_count.is_(None),
            )
        ).all()

        if not stubs:
            return 0

        # --- Fuente 1: Spotify batch ---
        spotify_data: Dict[str, Dict] = {}
        if spotify_token or (settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET):
            ids = [a.spotify_id for a in stubs]
            raw_spotify = None
            # Intentar con user token primero
            if spotify_token:
                try:
                    raw_spotify = SpotifyClient.get_artists(spotify_token, ids)
                    logger.info(f"Spotify (user token) enriqueció stubs")
                except Exception as e:
                    logger.warning(f"Spotify backfill con user token falló: {e}")
            # Fallback: Client Credentials si user token falló o no hay token
            if raw_spotify is None and settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
                try:
                    cc_token = SpotifyClient.get_client_credentials_token(
                        settings.SPOTIFY_CLIENT_ID,
                        settings.SPOTIFY_CLIENT_SECRET,
                    )
                    raw_spotify = SpotifyClient.get_artists(cc_token, ids)
                    logger.info("Spotify (CC token) usado como fallback para backfill de stubs")
                except Exception as e:
                    logger.warning(f"Spotify backfill CC token también falló: {e}")
                    raw_spotify = []
            for item in (raw_spotify or []):
                if not item:
                    continue
                images = item.get("images") or []
                spotify_data[item["id"]] = {
                    "popularity": item.get("popularity"),
                    "followers": (item.get("followers") or {}).get("total"),
                    "image_url": images[0]["url"] if images else None,
                    "genres": item.get("genres") or [],
                }
            logger.info(f"Spotify enriqueció {len(spotify_data)}/{len(stubs)} stubs")

        # --- Fuente 2: Last.fm (géneros y listeners) ---
        lastfm_data: Dict[str, Dict] = {}
        needs_lastfm = [
            a for a in stubs
            if not (spotify_data.get(a.spotify_id, {}).get("genres"))
            or not (spotify_data.get(a.spotify_id, {}).get("followers"))
        ]
        if settings.LASTFM_API_KEY and needs_lastfm:
            def _fetch_lfm(name: str) -> Dict:
                return {
                    "genres": EtlService.fetch_lastfm_genres(name),
                    "listeners": EtlService.fetch_lastfm_listeners(name),
                }
            with ThreadPoolExecutor(max_workers=10) as executor:
                fut_map = {executor.submit(_fetch_lfm, a.name): a.name for a in needs_lastfm}
                for fut in as_completed(fut_map):
                    name = fut_map[fut]
                    try:
                        lastfm_data[name] = fut.result()
                    except Exception:
                        lastfm_data[name] = {"genres": [], "listeners": None}

        # --- Fuente 3: play_count proporcional (último recurso) ---
        play_counts = dict(
            db.query(DimArtists.artist_id, sa_func.count(FactListeningHistory.id))
            .join(FactListeningHistory, FactListeningHistory.artist_id == DimArtists.artist_id)
            .group_by(DimArtists.artist_id)
            .all()
        )
        max_plays = max(play_counts.values(), default=1)

        updated = 0
        for artist in stubs:
            sp = spotify_data.get(artist.spotify_id, {})
            lfm = lastfm_data.get(artist.name, {})
            plays = play_counts.get(artist.artist_id, 1)

            # popularity: Spotify → log-scale play_count
            if artist.popularity is None or artist.image_url is None:
                if sp.get("popularity") is not None:
                    artist.popularity = sp["popularity"]
                elif artist.popularity is None:
                    log_plays = math.log1p(plays)
                    log_max = math.log1p(max_plays)
                    artist.popularity = max(10, round(log_plays * 100 / log_max))

            # followers_count: Spotify → Last.fm → estimado
            if artist.followers_count is None or artist.image_url is None:
                if sp.get("followers") is not None:
                    artist.followers_count = sp["followers"]
                elif artist.followers_count is None:
                    listeners = lfm.get("listeners") or 0
                    artist.followers_count = max(listeners, max(1, plays * 500))

            # image_url: Spotify (solo si está disponible)
            if artist.image_url is None and sp.get("image_url"):
                artist.image_url = sp["image_url"]

            # genres: Spotify → Last.fm → sentinel
            if not artist.genres or artist.genres == [""]:
                genres = sp.get("genres") or lfm.get("genres") or []
                artist.genres = genres if genres else [""]
                flag_modified(artist, "genres")

            updated += 1

        if stubs:
            db.commit()
        logger.info(f"Backfill artistas: {updated}/{len(stubs)} enriquecidos")
        return updated

    @staticmethod
    def enrich_artists_from_spotify(db: Session, spotify_ids: List[str], spotify_token: str) -> int:
        """
        Enriquece artistas con datos de Spotify.
        Intenta batch /v1/artists?ids=... primero; si devuelve 403 (restricción de
        Development Mode) cae back a /v1/search por nombre (siempre disponible).
        """
        if not spotify_ids:
            return 0

        search_token = spotify_token
        if settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
            try:
                search_token = SpotifyClient.get_client_credentials_token(
                    settings.SPOTIFY_CLIENT_ID,
                    settings.SPOTIFY_CLIENT_SECRET,
                )
            except Exception:
                pass

        # Intentar batch primero
        raw_map: Dict[str, Dict] = {}
        try:
            raw = SpotifyClient.get_artists(search_token, spotify_ids)
            for item in (raw or []):
                if item:
                    raw_map[item["id"]] = item
            logger.info(f"enrich_artists_from_spotify batch: {len(raw_map)}/{len(spotify_ids)}")
        except Exception as e:
            logger.warning(f"enrich_artists_from_spotify batch falló ({e}), usando search por nombre")

        # Fallback search para los que no se pudieron obtener por batch
        missing = [sid for sid in spotify_ids if sid not in raw_map]
        if missing:
            artists_to_search = db.query(DimArtists).filter(
                DimArtists.spotify_id.in_(missing)
            ).all()
            from concurrent.futures import ThreadPoolExecutor, as_completed as _ac
            def _search(a) -> tuple:
                try:
                    result = SpotifyClient.search_artist(search_token, a.name)
                    return a.spotify_id, result
                except Exception:
                    return a.spotify_id, None
            with ThreadPoolExecutor(max_workers=5) as executor:
                futs = {executor.submit(_search, a): a for a in artists_to_search}
                for fut in _ac(futs):
                    sid, result = fut.result()
                    if result:
                        raw_map[sid] = result
            logger.info(f"enrich_artists_from_spotify search fallback: {len(raw_map)}/{len(spotify_ids)} total")

        if not raw_map:
            return 0

        updated = 0
        for spotify_id in spotify_ids:
            item = raw_map.get(spotify_id)
            if not item:
                continue
            artist = db.query(DimArtists).filter_by(spotify_id=spotify_id).first()
            if not artist:
                continue
            images = item.get("images") or []
            pop = item.get("popularity")
            followers = (item.get("followers") or {}).get("total")
            if pop is not None:
                artist.popularity = pop
            if followers is not None:
                artist.followers_count = followers
            if images:
                artist.image_url = images[0]["url"]
            genres = item.get("genres") or []
            if genres and (not artist.genres or artist.genres == [""]):
                artist.genres = genres
                flag_modified(artist, "genres")
            updated += 1

        if updated:
            db.commit()
        logger.info(f"enrich_artists_from_spotify: {updated}/{len(spotify_ids)} artistas actualizados")
        return updated

    @staticmethod
    def backfill_track_popularity(db: Session, spotify_token: str) -> int:
        """
        Rellena popularity para todos los tracks del DWH que la tienen en NULL.

        Llama a GET /v1/tracks?ids=... con user token (fallback: Client Credentials).
        La API de recently-played no devuelve popularity, por eso la mayoría de tracks
        creados desde el historial quedan con este campo nulo hasta que este backfill corre.
        """
        stubs = db.query(DimTracks).filter(DimTracks.popularity.is_(None)).all()
        if not stubs:
            return 0

        raw = None
        try:
            raw = SpotifyClient.get_tracks(spotify_token, [t.spotify_id for t in stubs])
        except Exception as e:
            logger.warning(f"backfill_track_popularity con user token falló: {e}")
            if settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
                try:
                    cc_token = SpotifyClient.get_client_credentials_token(
                        settings.SPOTIFY_CLIENT_ID,
                        settings.SPOTIFY_CLIENT_SECRET,
                    )
                    raw = SpotifyClient.get_tracks(cc_token, [t.spotify_id for t in stubs])
                except Exception as e2:
                    logger.warning(f"backfill_track_popularity CC token también falló: {e2}")
                    return 0
            else:
                return 0

        updated = 0
        for item in (raw or []):
            if not item:
                continue
            pop = item.get("popularity")
            if pop is None:
                continue
            track = db.query(DimTracks).filter_by(spotify_id=item["id"]).first()
            if track and track.popularity is None:
                track.popularity = pop
                updated += 1

        if updated:
            db.commit()
        logger.info(f"backfill_track_popularity: {updated}/{len(stubs)} tracks actualizados")
        return updated

    @staticmethod
    def backfill_track_images(db: Session, spotify_token: str) -> int:
        """
        Actualiza album_image_url para todos los tracks del DWH que la tienen en NULL.

        Llama a GET /v1/tracks?ids=... con user token (fallback: Client Credentials).
        """
        stubs = db.query(DimTracks).filter(DimTracks.album_image_url.is_(None)).all()
        if not stubs:
            return 0

        raw = None
        try:
            raw = SpotifyClient.get_tracks(spotify_token, [t.spotify_id for t in stubs])
        except Exception as e:
            logger.warning(f"backfill_track_images con user token falló: {e}")
            if settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
                try:
                    cc_token = SpotifyClient.get_client_credentials_token(
                        settings.SPOTIFY_CLIENT_ID,
                        settings.SPOTIFY_CLIENT_SECRET,
                    )
                    raw = SpotifyClient.get_tracks(cc_token, [t.spotify_id for t in stubs])
                except Exception as e2:
                    logger.warning(f"backfill_track_images CC token también falló: {e2}")
                    return 0
            else:
                return 0

        updated = 0
        for item in (raw or []):
            if not item:
                continue
            album = item.get("album") or {}
            images = album.get("images") or []
            if not images:
                continue
            track = db.query(DimTracks).filter_by(spotify_id=item["id"]).first()
            if track:
                track.album_image_url = images[0]["url"]
                updated += 1

        if updated:
            db.commit()
        logger.info(f"backfill_track_images: {updated}/{len(stubs)} tracks actualizados")
        return updated

    # ============ LOAD ============

    @staticmethod
    def load_user(db: Session, user_data: Dict[str, Any], access_token: str, refresh_token: Optional[str]) -> str:
        """
        Inserta o actualiza el registro del usuario en dim_users.

        Args:
            db (Session): Sesión de SQLAlchemy.
            user_data (Dict[str, Any]): Dict normalizado con los campos de dim_users.
            access_token (str): Access token de Spotify a persistir.
            refresh_token (Optional[str]): Refresh token de Spotify; si es None no se sobreescribe el existente.

        Returns:
            str: spotify_id del usuario cargado.
        """
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
    def load_artists(db: Session, artists_data: List[Dict[str, Any]], full_run: bool = True) -> Tuple[int, int]:
        """
        Inserta artistas nuevos y, en ETL full, actualiza los existentes en dim_artists.

        En modo incremental (full_run=False) solo se insertan artistas nuevos; los
        existentes no se tocan para evitar llamadas innecesarias a Last.fm.
        """
        logger.info(f"Cargando {len(artists_data)} artistas (full_run={full_run})...")
        new_count = 0
        updated_count = 0
        for artist in artists_data:
            existing = db.query(DimArtists).filter_by(spotify_id=artist["spotify_id"]).first()

            if not existing:
                incoming_genres = artist.get("genres") or []
                if not incoming_genres:
                    fetched = EtlService.fetch_lastfm_genres(artist["name"])
                    incoming_genres = fetched if fetched else [""]
                artist["genres"] = incoming_genres
                db.add(DimArtists(**artist))
                new_count += 1
            else:
                # Siempre actualizar campos de Spotify (no requieren Last.fm)
                if artist.get("popularity") is not None:
                    existing.popularity = artist["popularity"]
                if artist.get("followers_count") is not None:
                    existing.followers_count = artist["followers_count"]
                if artist.get("image_url"):
                    existing.image_url = artist["image_url"]
                # Géneros via Last.fm: solo en full_run
                if full_run:
                    incoming_genres = artist.get("genres") or []
                    if not incoming_genres:
                        fetched = EtlService.fetch_lastfm_genres(artist["name"])
                        incoming_genres = fetched if fetched else [""]
                    existing.genres = incoming_genres if incoming_genres else (existing.genres or [""])
                    flag_modified(existing, "genres")
                updated_count += 1
        db.commit()
        logger.info(f"Artistas cargados: {new_count} nuevos, {updated_count} actualizados")
        return new_count, updated_count

    @staticmethod
    def load_tracks(db: Session, tracks_data: List[Dict[str, Any]], full_run: bool = True) -> Tuple[int, int]:
        """
        Inserta canciones nuevas en dim_tracks, creando un artista básico si no existe en DWH.

        En modo incremental (full_run=False) solo se insertan canciones nuevas; las
        existentes no se actualizan para reducir escrituras innecesarias.
        """
        logger.info(f"Cargando {len(tracks_data)} canciones (full_run={full_run})...")
        new_count = 0
        updated_count = 0
        new_tracks_detail: List[Dict[str, Any]] = []
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
                new_tracks_detail.append({
                    "name": track.get("name") or "",
                    "artist_name": track.get("artist_name") or "",
                    "album_name": track.get("album_name"),
                    "album_image_url": track.get("album_image_url"),
                    "spotify_id": track.get("spotify_id"),
                })
            elif full_run:
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
                updated_count += 1
        db.commit()
        logger.info(f"Canciones cargadas: {new_count} nuevas, {updated_count} actualizadas")
        return new_count, updated_count, new_tracks_detail

    @staticmethod
    def load_history(db: Session, spotify_user_id: str, history_data: List[Dict[str, Any]], spotify_token: Optional[str] = None) -> Tuple[int, int]:
        """
        Inserta registros de reproducción en fact_listening_history, deduplicando por (user_id, track_id, played_at).

        Args:
            db (Session): Sesión de SQLAlchemy.
            spotify_user_id (str): spotify_id del usuario propietario del historial.
            history_data (List[Dict[str, Any]]): Lista de items normalizados por transform_history.

        Returns:
            Tuple[int, int]: (new_count, skipped_count) — registros insertados y omitidos (duplicados o track no encontrado).
        """
        logger.info(f"Cargando {len(history_data)} registros de historial...")
        new_count = 0
        skipped_count = 0
        new_history_detail: List[Dict[str, Any]] = []
        new_catalog_from_history: List[Dict[str, Any]] = []
        new_stub_artist_ids: List[str] = []
        user = db.query(DimUsers).filter_by(spotify_id=spotify_user_id).first()
        if not user:
            logger.error(f"Usuario no encontrado: {spotify_user_id}")
            return 0, 0, [], []

        for item in history_data:
            track = db.query(DimTracks).filter_by(
                spotify_id=item["spotify_track_id"]
            ).first()

            if track and track.popularity is None and item.get("popularity") is not None:
                track.popularity = item["popularity"]
            if track and track.album_image_url is None and item.get("album_image_url"):
                track.album_image_url = item["album_image_url"]

            if not track:
                # Canción fuera del top 50 — crearla con los datos de recently-played.
                # Usamos savepoint (begin_nested) para que un fallo de constraint
                # aquí no cancele el commit exterior con las demás inserciones.
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
                            new_stub_artist_ids.append(spotify_artist_id)

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
                        new_catalog_from_history.append({
                            "name": item.get("track_name") or "",
                            "artist_name": item.get("artist_name") or "",
                            "album_name": item.get("album_name"),
                            "album_image_url": item.get("album_image_url"),
                            "spotify_id": item.get("spotify_track_id"),
                        })
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

            # Pre-chequeo de duplicado por (user_id, played_at)
            existing_record = db.query(FactListeningHistory).filter_by(
                user_id=user.user_id,
                played_at=item["played_at"],
            ).first()

            if existing_record:
                skipped_count += 1
                continue

            db.add(FactListeningHistory(
                user_id=user.user_id,
                track_id=track.track_id,
                artist_id=artist_id,
                played_at=item["played_at"],
                hour_of_day=item.get("hour_of_day"),
                day_of_week=item.get("day_of_week"),
                context_type=item.get("context_type"),
            ))
            new_count += 1
            new_history_detail.append({
                "track_name": item.get("track_name", ""),
                "artist_name": item.get("artist_name", ""),
                "album_image_url": item.get("album_image_url"),
                "played_at": item["played_at"].isoformat(),
            })

        if new_stub_artist_ids and spotify_token:
            logger.info(f"Enriqueciendo {len(new_stub_artist_ids)} artistas stub desde Spotify...")
            EtlService.enrich_artists_from_spotify(db, new_stub_artist_ids, spotify_token)

        db.commit()
        logger.info(f"Historial cargado: {new_count} nuevos, {skipped_count} saltados")
        return new_count, skipped_count, new_history_detail, new_catalog_from_history


    @staticmethod
    def fetch_lastfm_listeners(artist_name: str) -> Optional[int]:
        """
        Obtiene el número de listeners de un artista desde Last.fm.
        """
        if not settings.LASTFM_API_KEY:
            return None
        try:
            response = requests.get(
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
            data = response.json()
            listeners = data.get("artist", {}).get("stats", {}).get("listeners")
            return int(listeners) if listeners else None
        except Exception as e:
            logger.warning(f"Last.fm listeners fallo para '{artist_name}': {e}")
            return None
        

    @staticmethod
    def fetch_lastfm_playcount(artist_name: str) -> Optional[int]:
        if not settings.LASTFM_API_KEY:
            return None
        try:
            response = requests.get(
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
            data = response.json()
            playcount = data.get("artist", {}).get("stats", {}).get("playcount")
            return int(playcount) if playcount else None
        except Exception as e:
            logger.warning(f"Last.fm playcount fallo para '{artist_name}': {e}")
            return None
        
    @staticmethod
    def fetch_lastfm_track_playcount(track_name: str, artist_name: str) -> Optional[int]:
        if not settings.LASTFM_API_KEY:
            return None
        try:
            response = requests.get(
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
            data = response.json()
            playcount = data.get("track", {}).get("playcount")
            return int(playcount) if playcount else None
        except Exception as e:
            logger.warning(f"Last.fm track playcount fallo para '{track_name}': {e}")
            return None