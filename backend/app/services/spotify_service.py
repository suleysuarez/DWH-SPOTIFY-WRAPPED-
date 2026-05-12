"""
Servicio para interactuar con Spotify API.
Incluye funciones para obtener token, datos de usuario, artistas, canciones, historial.
"""

import requests
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class SpotifyService:
    """Cliente para Spotify API."""

    BASE_URL = "https://api.spotify.com/v1"
    AUTH_URL = "https://accounts.spotify.com"

    @staticmethod
    def get_access_token(code: str, code_verifier: str) -> Dict[str, Any]:
        """
        Intercambia authorization code por access token (PKCE flow).
        
        Args:
            code: Authorization code de Spotify
            code_verifier: Code verifier generado en el frontend
            
        Returns:
            Dict con access_token, refresh_token, expires_in
        """
        payload = {
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "code_verifier": code_verifier,
        }
        response = requests.post(f"{SpotifyService.AUTH_URL}/api/token", data=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """
        Renueva el access token usando refresh token.
        
        Args:
            refresh_token: Refresh token del usuario
            
        Returns:
            Dict con nuevo access_token y expires_in
        """
        payload = {
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        response = requests.post(f"{SpotifyService.AUTH_URL}/api/token", data=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_current_user(access_token: str) -> Dict[str, Any]:
        """
        Obtiene datos del usuario autenticado.
        
        Args:
            access_token: Access token válido
            
        Returns:
            Dict con datos del usuario (id, display_name, email, country, followers, images, product)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{SpotifyService.BASE_URL}/me", headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_top_artists(access_token: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Obtiene top artistas del usuario.
        
        Args:
            access_token: Access token válido
            limit: Número de artistas (máx 50)
            offset: Offset para paginación
            
        Returns:
            Dict con items (artistas)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"limit": limit, "offset": offset, "time_range": "medium_term"}
        response = requests.get(
            f"{SpotifyService.BASE_URL}/me/top/artists",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_top_tracks(access_token: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Obtiene top canciones del usuario.
        
        Args:
            access_token: Access token válido
            limit: Número de canciones (máx 50)
            offset: Offset para paginación
            
        Returns:
            Dict con items (canciones)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"limit": limit, "offset": offset, "time_range": "medium_term"}
        response = requests.get(
            f"{SpotifyService.BASE_URL}/me/top/tracks",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_recently_played(
        access_token: str,
        limit: int = 50,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene historial de reproducción reciente.
        
        Args:
            access_token: Access token válido
            limit: Número de items (máx 50)
            before: Timestamp en ms para paginación hacia atrás
            
        Returns:
            Dict con items (historial) y cursores
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"limit": limit}
        if before:
            params["before"] = before
        
        response = requests.get(
            f"{SpotifyService.BASE_URL}/me/player/recently_played",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
