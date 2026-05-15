"""
etl_service.py (LEGACY — app/services/) — Orquestador ETL original.

⚠️  ARCHIVO LEGACY: Usado por los routers legacy (app/routers/) que NO están
    montados en la app activa. La versión activa es app/v1/services/etl_service.py.

Diferencias con la versión activa (v1):
- extract_recently_played() acepta cursor_next_ms (nombrado diferente a after).
- load_user() retorna user_id (int) en lugar de spotify_id (str).
- load_artists/tracks no actualiza géneros/popularidad al hacer upsert.
- No incluye la lógica de artist fallback cuando falta el artista de un track.
- Usa SpotifyClient de v1 para las llamadas HTTP (no SpotifyService de legacy).
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import DimUsers, DimArtists, DimTracks, FactListeningHistory, EtlAudit
from app.v1.services.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)


class EtlService:
    """Orquestador del pipeline ETL."""

    # ============ EXTRACT ============

    @staticmethod
    def extract_user(token: str) -> Dict[str, Any]:
        """
        Llama al endpoint /v1/me de Spotify y retorna la lista cruda.

        Args:
            token (str): Access token de Spotify (Bearer).

        Returns:
            Dict[str, Any]: Objeto usuario en formato JSON crudo de Spotify.
        """
        logger.info("Extrayendo datos del usuario...")
        user = SpotifyClient.get_current_user(token)
        logger.info(f"Usuario extraído: {user['id']}")
        return user

    @staticmethod
    def extract_top_artists(token: str) -> List[Dict[str, Any]]:
        """
        Llama al endpoint /v1/me/top/artists de Spotify y retorna la lista cruda.

        Args:
            token (str): Access token de Spotify (Bearer).

        Returns:
            List[Dict[str, Any]]: Lista de objetos artista en formato JSON crudo de Spotify.
        """
        logger.info("Extrayendo top artistas...")
        response = SpotifyClient.get_top_artists(token, limit=50)
        artists = (response or {}).get("items", [])
        logger.info(f"Artistas extraídos: {len(artists)}")
        return artists

    @staticmethod
    def extract_top_tracks(token: str) -> List[Dict[str, Any]]:
        """
        Llama al endpoint /v1/me/top/tracks de Spotify y retorna la lista cruda.

        Args:
            token (str): Access token de Spotify (Bearer).

        Returns:
            List[Dict[str, Any]]: Lista de objetos canción en formato JSON crudo de Spotify.
        """
        logger.info("Extrayendo top canciones...")
        response = SpotifyClient.get_top_tracks(token, limit=50)
        tracks = (response or {}).get("items", [])
        logger.info(f"Canciones extraídas: {len(tracks)}")
        return tracks

    @staticmethod
    def extract_recently_played(token: str, after: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Llama al endpoint /v1/me/player/recently-played de Spotify y retorna la lista cruda.

        Args:
            token (str): Access token de Spotify (Bearer).
            after (str): Timestamp en ms para paginación hacia atrás.

        Returns:
            Tuple[List[Dict[str, Any]], Optional[str]]: (items, cursor_next).
        """
        logger.info("Extrayendo historial de reproducción...")
        response = SpotifyClient.get_recently_played(token, limit=50, after=after)
        # Spotify puede devolver None al llegar al final del historial
        items = (response or {}).get("items", [])
        next_cursor = (response or {}).get("cursors", {}).get("after")
        logger.info(f"Historial extraído: {len(items)} items, next_cursor: {next_cursor}")
        return items, next_cursor

    # ============ TRANSFORM ============

    @staticmethod
    def transform_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza datos del usuario para cargar en dwh.dim_users.

        Args:
            user_data (Dict[str, Any]): Objeto usuario crudo de Spotify.

        Returns:
            Dict[str, Any]: Objeto normalizado para dim_users.
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
        Normaliza artistas para cargar en dwh.dim_artists.

        Args:
            artists_data (List[Dict[str, Any]]): Lista de artistas crudos de Spotify.

        Returns:
            List[Dict[str, Any]]: Lista de artistas normalizados.
        """
        logger.info(f"Transformando {len(artists_data)} artistas...")
        transformed = []
        for artist in artists_data:
            transformed.append({
                "spotify_id": artist["id"],
                "name": artist["name"],
                "popularity": artist.get("popularity"),
                "followers_count": artist.get("followers", {}).get("total"),
                "genres": artist.get("genres", []),
            })
        logger.info(f"Artistas transformados: {len(transformed)}")
        return transformed

    @staticmethod
    def transform_tracks(tracks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normaliza canciones para cargar en dwh.dim_tracks.

        Args:
            tracks_data (List[Dict[str, Any]]): Lista de canciones crudas de Spotify.

        Returns:
            List[Dict[str, Any]]: Lista de canciones normalizadas.
        """
        logger.info(f"Transformando {len(tracks_data)} canciones...")
        transformed = []
        for track in tracks_data:
            album = track.get("album", {})
            transformed.append({
                "spotify_id": track["id"],
                "name": track["name"],
                "spotify_artist_id": track["artists"][0]["id"] if track.get("artists") else None,
                "album_name": album.get("name"),
                "duration_ms": track.get("duration_ms"),
                "popularity": track.get("popularity"),
                "explicit": track.get("explicit", False),
            })
        logger.info(f"Canciones transformadas: {len(transformed)}")
        return transformed

    @staticmethod
    def transform_history(history_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normaliza historial para cargar en dwh.fact_listening_history.

        Args:
            history_data (List[Dict[str, Any]]): Lista de items del historial crudo de Spotify.

        Returns:
            List[Dict[str, Any]]: Lista de items normalizados.
        """
        logger.info(f"Transformando {len(history_data)} registros de historial...")
        transformed = []
        for item in history_data:
            track = item.get("track", {})
            context = item.get("context", {})

            # Parsear played_at
            played_at_str = item.get("played_at", "").replace("Z", "+00:00")
            played_at = datetime.fromisoformat(played_at_str)

            transformed.append({
                "spotify_track_id": track.get("id"),
                "spotify_artist_id": track.get("artists", [{}])[0].get("id"),
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
        Carga usuario en dwh.dim_users (upsert).

        Args:
            db (Session): Sesión de BD.
            user_data (Dict[str, Any]): Datos transformados del usuario.
            access_token (str): Access token de Spotify.
            refresh_token (Optional[str]): Refresh token de Spotify.

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
        Carga artistas en dwh.dim_artists (upsert).

        Args:
            db (Session): Sesión de BD.
            artists_data (List[Dict[str, Any]]): Datos transformados de artistas.

        Returns:
            Tuple[int, int]: (nuevos, saltados).
        """
        logger.info(f"Cargando {len(artists_data)} artistas...")
        new_count = 0
        skipped_count = 0

        for artist in artists_data:
            existing = db.query(DimArtists).filter_by(spotify_id=artist["spotify_id"]).first()
            if not existing:
                db.add(DimArtists(**artist))
                new_count += 1
            else:
                skipped_count += 1

        db.commit()
        logger.info(f"Artistas cargados: {new_count} nuevos, {skipped_count} saltados")
        return new_count, skipped_count

    @staticmethod
    def load_tracks(db: Session, tracks_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Carga canciones en dwh.dim_tracks (upsert).

        Args:
            db (Session): Sesión de BD.
            tracks_data (List[Dict[str, Any]]): Datos transformados de canciones.

        Returns:
            Tuple[int, int]: (nuevos, saltados).
        """
        logger.info(f"Cargando {len(tracks_data)} canciones...")
        new_count = 0
        skipped_count = 0

        for track in tracks_data:
            existing = db.query(DimTracks).filter_by(spotify_id=track["spotify_id"]).first()
            if not existing:
                artist = db.query(DimArtists).filter_by(
                    spotify_id=track["spotify_artist_id"]
                ).first()

                if not artist:
                    logger.warning(f"Artista no encontrado para track {track['spotify_id']}")
                    continue

                track["artist_id"] = artist.artist_id
                del track["spotify_artist_id"]

                db.add(DimTracks(**track))
                new_count += 1
            else:
                skipped_count += 1

        db.commit()
        logger.info(f"Canciones cargadas: {new_count} nuevas, {skipped_count} saltadas")
        return new_count, skipped_count

    @staticmethod
    def load_history(db: Session, spotify_user_id: str, history_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Carga historial en dwh.fact_listening_history (upsert).

        Args:
            db (Session): Sesión de BD.
            spotify_user_id (str): ID de Spotify del usuario.
            history_data (List[Dict[str, Any]]): Datos transformados del historial.

        Returns:
            Tuple[int, int]: (nuevos, saltados).
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
                logger.warning(f"Track no encontrado: {item['spotify_track_id']}")
                continue

            artist = db.query(DimArtists).filter_by(
                spotify_id=item["spotify_artist_id"]
            ).first()

            if not artist:
                logger.warning(f"Artista no encontrado: {item['spotify_artist_id']}")
                continue

            existing = db.query(FactListeningHistory).filter_by(
                user_id=user.user_id,
                track_id=track.track_id,
                played_at=item["played_at"],
            ).first()

            if not existing:
                db.add(FactListeningHistory(
                    user_id=user.user_id,
                    track_id=track.track_id,
                    artist_id=artist.artist_id,
                    played_at=item["played_at"],
                    hour_of_day=item.get("hour_of_day"),
                    day_of_week=item.get("day_of_week"),
                    context_type=item.get("context_type"),
                ))
                new_count += 1
            else:
                skipped_count += 1

        db.commit()
        logger.info(f"Historial cargado: {new_count} nuevos, {skipped_count} saltados")
        return new_count, skipped_count