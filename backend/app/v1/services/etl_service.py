"""
filename: etl_service.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Orquestador del pipeline ETL (versión activa). Clase EtlService con métodos
             agrupados en Extract (Spotify API), Transform (normalización) y Load (upsert DWH).
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.models import DimUsers, DimArtists, DimTracks, FactListeningHistory
from app.v1.services.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)


class EtlService:
    """Orquestador del pipeline ETL."""

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
    def load_artists(db: Session, artists_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Inserta artistas nuevos y actualiza los existentes en dim_artists.

        Args:
            db (Session): Sesión de SQLAlchemy.
            artists_data (List[Dict[str, Any]]): Lista de artistas normalizados por transform_artists.

        Returns:
            Tuple[int, int]: (new_count, updated_count) — cantidad de artistas insertados y actualizados.
        """
        logger.info(f"Cargando {len(artists_data)} artistas...")
        new_count = 0
        updated_count = 0
        for artist in artists_data:
            existing = db.query(DimArtists).filter_by(spotify_id=artist["spotify_id"]).first()
            if not existing:
                db.add(DimArtists(**artist))
                new_count += 1
            else:
                # Actualizar campos que pueden cambiar
                existing.genres = list(artist.get("genres", []))
                flag_modified(existing, "genres")
                existing.popularity = artist.get("popularity", existing.popularity)
                existing.followers_count = artist.get("followers_count", existing.followers_count)
                if artist.get("image_url"):
                    existing.image_url = artist["image_url"]
                updated_count += 1
        db.commit()
        logger.info(f"Artistas cargados: {new_count} nuevos, {updated_count} actualizados")
        return new_count, updated_count

    @staticmethod
    def load_tracks(db: Session, tracks_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Inserta canciones nuevas en dim_tracks, creando un artista básico si no existe en DWH.

        Args:
            db (Session): Sesión de SQLAlchemy.
            tracks_data (List[Dict[str, Any]]): Lista de canciones normalizadas por transform_tracks.

        Returns:
            Tuple[int, int]: (new_count, skipped_count) — canciones insertadas y omitidas (ya existían).
        """
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
                # Actualizar campos que pueden estar en NULL por datos históricos
                existing.popularity = track.get("popularity", existing.popularity)
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
        return new_count, updated_count

    @staticmethod
    def load_history(db: Session, spotify_user_id: str, history_data: List[Dict[str, Any]]) -> Tuple[int, int]:
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
        user = db.query(DimUsers).filter_by(spotify_id=spotify_user_id).first()
        if not user:
            logger.error(f"Usuario no encontrado: {spotify_user_id}")
            return 0, 0

        for item in history_data:
            track = db.query(DimTracks).filter_by(
                spotify_id=item["spotify_track_id"]
            ).first()

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
                            artist = DimArtists(
                                spotify_id=spotify_artist_id,
                                name=item.get("artist_name", "Desconocido"),
                                genres=[],
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

            # ON CONFLICT DO NOTHING resuelve dos bugs a la vez:
            # 1. Elimina la query de pre-chequeo (era N+1 consultas).
            # 2. Si dos canciones llegan con el mismo played_at (timestamps repetidos
            #    de Spotify), la segunda se ignora en vez de lanzar IntegrityError
            #    y revertir TODOS los inserts del commit.
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
