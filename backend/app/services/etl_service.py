"""
Servicio ETL: extract, transform, load.
Pipeline completo para sincronizar datos de Spotify al DWH.
"""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import (
    DimUsers, DimArtists, DimTracks, FactListeningHistory, EtlAudit
)
from app.services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)


class EtlService:
    """Orquestador del pipeline ETL."""

    @staticmethod
    def extract_user(access_token: str) -> Dict[str, Any]:
        """
        Extrae datos del usuario autenticado.
        
        Phase: EXTRACT_USER
        """
        logger.info("Extrayendo datos del usuario...")
        user = SpotifyService.get_current_user(access_token)
        logger.info(f"Usuario extraído: {user['id']}")
        return user

    @staticmethod
    def extract_top_artists(access_token: str) -> List[Dict[str, Any]]:
        """
        Extrae top 50 artistas del usuario.
        
        Phase: EXTRACT_ARTISTS
        """
        logger.info("Extrayendo top artistas...")
        response = SpotifyService.get_top_artists(access_token, limit=50)
        artists = response.get("items", [])
        logger.info(f"Artistas extraídos: {len(artists)}")
        return artists

    @staticmethod
    def extract_top_tracks(access_token: str) -> List[Dict[str, Any]]:
        """
        Extrae top 50 canciones del usuario.
        
        Phase: EXTRACT_TRACKS
        """
        logger.info("Extrayendo top canciones...")
        response = SpotifyService.get_top_tracks(access_token, limit=50)
        tracks = response.get("items", [])
        logger.info(f"Canciones extraídas: {len(tracks)}")
        return tracks

    @staticmethod
    def extract_recently_played(
        access_token: str,
        cursor_next_ms: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Extrae historial de reproducción reciente.
        
        Phase: EXTRACT_HISTORY
        Usa cursor_next_ms para carga incremental.
        """
        logger.info("Extrayendo historial de reproducción...")
        response = SpotifyService.get_recently_played(access_token, limit=50, before=cursor_next_ms)
        items = response.get("items", [])
        next_cursor = response.get("cursors", {}).get("before")
        logger.info(f"Historial extraído: {len(items)} items, next_cursor: {next_cursor}")
        return items, next_cursor

    @staticmethod
    def transform_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma datos del usuario para cargar en dim_users.
        
        Phase: TRANSFORM_USER
        """
        logger.info("Transformando datos del usuario...")
        images = user_data.get("images", [])
        images_url = images[0]["url"] if images else None
        
        transformed = {
            "spotify_id": user_data["id"],
            "display_name": user_data.get("display_name"),
            "email": user_data.get("email"),
            "country": user_data.get("country"),
            "followers": user_data.get("followers", {}).get("total", 0),
            "product": user_data.get("product", "free"),
            "images_url": images_url,
        }
        logger.info(f"Usuario transformado: {transformed['spotify_id']}")
        return transformed

    @staticmethod
    def transform_artists(artists_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforma artistas para cargar en dim_artists.
        
        Phase: TRANSFORM_ARTISTS
        """
        logger.info(f"Transformando {len(artists_data)} artistas...")
        transformed = []
        for artist in artists_data:
            images = artist.get("images", [])
            images_url = images[0]["url"] if images else None
            
            transformed.append({
                "spotify_id": artist["id"],
                "name": artist["name"],
                "genres": json.dumps(artist.get("genres", [])),
                "popularity": artist.get("popularity"),
                "images_url": images_url,
            })
        logger.info(f"Artistas transformados: {len(transformed)}")
        return transformed

    @staticmethod
    def transform_tracks(tracks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforma canciones para cargar en dim_tracks.
        
        Phase: TRANSFORM_TRACKS
        """
        logger.info(f"Transformando {len(tracks_data)} canciones...")
        transformed = []
        for track in tracks_data:
            album = track.get("album", {})
            images = album.get("images", [])
            album_image_url = images[0]["url"] if images else None
            
            transformed.append({
                "spotify_id": track["id"],
                "name": track["name"],
                "spotify_artist_id": track["artists"][0]["id"] if track.get("artists") else None,
                "album_name": album.get("name"),
                "album_image_url": album_image_url,
                "duration_ms": track.get("duration_ms"),
                "explicit": track.get("explicit", False),
            })
        logger.info(f"Canciones transformadas: {len(transformed)}")
        return transformed

    @staticmethod
    def transform_history(history_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforma historial de reproducción para cargar en fact_listening_history.
        
        Phase: TRANSFORM_HISTORY
        """
        logger.info(f"Transformando {len(history_data)} registros de historial...")
        transformed = []
        for item in history_data:
            track = item.get("track", {})
            context = item.get("context", {})
            
            # Manejo de context_type nulo
            context_type = context.get("type") if context else "unknown"
            context_name = context.get("external_urls", {}).get("spotify", "").split("/")[-1] if context else None
            
            # Reemplazar Z por +00:00 para parsear correctamente ISO 8601
            played_at_str = item.get("played_at", "").replace("Z", "+00:00")
            
            transformed.append({
                "spotify_track_id": track.get("id"),
                "spotify_artist_id": track.get("artists", [{}])[0].get("id"),
                "played_at": played_at_str,
                "context_type": context_type,
                "context_name": context_name,
            })
        logger.info(f"Historial transformado: {len(transformed)}")
        return transformed

    @staticmethod
    def load_user(db: Session, user_data: Dict[str, Any], access_token: str, refresh_token: Optional[str]) -> int:
        """
        Carga usuario en dim_users (upsert).
        
        Phase: LOAD_USER
        Retorna user_id interno.
        """
        logger.info(f"Cargando usuario {user_data['spotify_id']}...")
        
        user = db.query(DimUsers).filter_by(spotify_id=user_data["spotify_id"]).first()
        
        if user:
            # Update
            for key, value in user_data.items():
                setattr(user, key, value)
            user.spotify_access_token = access_token
            if refresh_token:
                user.spotify_refresh_token = refresh_token
            user.token_expires_at = datetime.utcnow()  # Simplificado; en producción calcular con exp
        else:
            # Insert
            user = DimUsers(
                **user_data,
                spotify_access_token=access_token,
                spotify_refresh_token=refresh_token,
                token_expires_at=datetime.utcnow(),
            )
            db.add(user)
        
        db.commit()
        logger.info(f"Usuario cargado: user_id={user.user_id}")
        return user.user_id

    @staticmethod
    def load_artists(db: Session, artists_data: List[Dict[str, Any]]) -> int:
        """
        Carga artistas en dim_artists (upsert con ON CONFLICT DO NOTHING).
        
        Phase: LOAD_ARTISTS
        Retorna cantidad de artistas cargados.
        """
        logger.info(f"Cargando {len(artists_data)} artistas...")
        loaded = 0
        
        for artist in artists_data:
            existing = db.query(DimArtists).filter_by(spotify_id=artist["spotify_id"]).first()
            if not existing:
                db.add(DimArtists(**artist))
                loaded += 1
        
        db.commit()
        logger.info(f"Artistas cargados: {loaded}")
        return loaded

    @staticmethod
    def load_tracks(db: Session, tracks_data: List[Dict[str, Any]]) -> int:
        """
        Carga canciones en dim_tracks (upsert).
        Requiere lookup de artist_id interno desde spotify_artist_id.
        
        Phase: LOAD_TRACKS
        Retorna cantidad de canciones cargadas.
        """
        logger.info(f"Cargando {len(tracks_data)} canciones...")
        loaded = 0
        
        for track in tracks_data:
            existing = db.query(DimTracks).filter_by(spotify_id=track["spotify_id"]).first()
            if not existing:
                # Lookup artist_id interno
                artist = db.query(DimArtists).filter_by(
                    spotify_id=track["spotify_artist_id"]
                ).first()
                
                if not artist:
                    logger.warning(f"Artista no encontrado para track {track['spotify_id']}")
                    continue
                
                track["artist_id"] = artist.artist_id
                del track["spotify_artist_id"]
                
                db.add(DimTracks(**track))
                loaded += 1
        
        db.commit()
        logger.info(f"Canciones cargadas: {loaded}")
        return loaded

    @staticmethod
    def load_history(db: Session, user_id: int, history_data: List[Dict[str, Any]]) -> int:
        """
        Carga historial en fact_listening_history (upsert).
        Requiere lookups de track_id y artist_id internos.
        
        Phase: LOAD_HISTORY
        Retorna cantidad de registros cargados.
        """
        logger.info(f"Cargando {len(history_data)} registros de historial...")
        loaded = 0
        
        for item in history_data:
            # Lookup track_id y artist_id internos
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
            
            # Verificar si ya existe
            existing = db.query(FactListeningHistory).filter_by(
                user_id=user_id,
                track_id=track.track_id,
                played_at=item["played_at"],
            ).first()
            
            if not existing:
                db.add(FactListeningHistory(
                    user_id=user_id,
                    track_id=track.track_id,
                    artist_id=artist.artist_id,
                    played_at=item["played_at"],
                    context_type=item.get("context_type"),
                    context_name=item.get("context_name"),
                ))
                loaded += 1
        
        db.commit()
        logger.info(f"Registros de historial cargados: {loaded}")
        return loaded
