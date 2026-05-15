"""
filename: etl_service.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.1
description: Servicio ETL: orquesta las 3 fases (extract, transform, load) del pipeline de sincronizacion con Spotify.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import text
from app.models.models import DimUsers, DimArtists, DimTracks, FactListeningHistory, EtlAudit
from app.v1.services.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)


class EtlService:
    """Orquestador del pipeline ETL."""

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
        transformed = {
            "spotify_id": user_data["id"],
            "display_name": user_data.get("display_name"),
            "email": user_data.get("email"),
            "country": user_data.get("country"),
            "followers": user_data.get("followers", {}).get("total", 0),
            "product": user_data.get("product", "free"),
        }
        logger.info(f"Usuario transformado: {transformed['spotify_id']}")
        return transformed

    @staticmethod
    def transform_artists(artists_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
            context = item.get("context", {})
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
        skipped_count = 0
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
                skipped_count += 1
        db.commit()
        logger.info(f"Artistas cargados: {new_count} nuevos, {skipped_count} actualizados")
        return new_count, skipped_count

    @staticmethod
    def load_tracks(db: Session, tracks_data: List[Dict[str, Any]]) -> Tuple[int, int]:
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
                if existing.artist_id is None:
                    artist = db.query(DimArtists).filter_by(
                        spotify_id=track["spotify_artist_id"]
                    ).first()
                    if artist:
                        existing.artist_id = artist.artist_id
                        logger.info(f"Reparado artist_id para track {track['spotify_id']}")
                skipped_count += 1
        db.commit()
        logger.info(f"Canciones cargadas: {new_count} nuevas, {skipped_count} saltadas")
        return new_count, skipped_count

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
            if not track:
                logger.warning(f"Track no encontrado: {item['spotify_track_id']}, saltando...")
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

            existing = db.query(FactListeningHistory).filter_by(
                user_id=user.user_id,
                track_id=track.track_id,
                played_at=item["played_at"],
            ).first()
            if not existing:
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
            else:
                skipped_count += 1
        db.commit()
        logger.info(f"Historial cargado: {new_count} nuevos, {skipped_count} saltados")
        return new_count, skipped_count
