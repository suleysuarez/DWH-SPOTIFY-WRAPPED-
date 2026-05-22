"""
filename: spotify_client.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Cliente HTTP estático para la Spotify Web API. Consume /me, /me/top/artists,
             /me/top/tracks y /me/player/recently-played para el pipeline ETL.
"""

import base64
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Cliente HTTP para Spotify Web API."""

    BASE_URL = "https://api.spotify.com/v1"
    AUTH_URL = "https://accounts.spotify.com"

    @staticmethod
    def get_access_token(code: str, code_verifier: str, client_id: str, client_secret: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Intercambia authorization code por access token (PKCE flow).

        Args:
            code (str): Authorization code de Spotify.
            code_verifier (str): Code verifier generado en el frontend.
            client_id (str): Client ID de la aplicación.
            client_secret (str): Client Secret de la aplicación.
            redirect_uri (str): Redirect URI registrada en Spotify.

        Returns:
            Dict[str, Any]: Dict con access_token, refresh_token, expires_in.
        """
        payload = {
            "client_id": client_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
        response = requests.post(f"{SpotifyClient.AUTH_URL}/api/token", data=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> Dict[str, Any]:
        """
        Renueva el access token usando refresh token (PKCE flow).

        Args:
            refresh_token (str): Refresh token del usuario.
            client_id (str): Client ID de la aplicación.
            client_secret (str): Client Secret (no se envía — PKCE no lo requiere y causa 400).

        Returns:
            Dict[str, Any]: Dict con nuevo access_token y expires_in.
        """
        # PKCE flow: client_secret NO debe enviarse; incluirlo causa 400 Bad Request.
        payload = {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        response = requests.post(f"{SpotifyClient.AUTH_URL}/api/token", data=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_client_credentials_token(client_id: str, client_secret: str) -> str:
        """
        Obtiene un token de acceso via Client Credentials flow (sin usuario).

        Necesario para endpoints de catálogo como GET /v1/artists?ids=... que
        devuelven 403 con tokens de usuario PKCE en modo desarrollo de Spotify.

        Args:
            client_id (str): Client ID de la aplicación.
            client_secret (str): Client Secret de la aplicación.

        Returns:
            str: Access token de Client Credentials.
        """
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        response = requests.post(
            f"{SpotifyClient.AUTH_URL}/api/token",
            headers={"Authorization": f"Basic {credentials}"},
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        return response.json()["access_token"]

    @staticmethod
    def get_current_user(token: str) -> Dict[str, Any]:
        """
        Obtiene datos del usuario autenticado.

        Args:
            token (str): Access token válido de Spotify.

        Returns:
            Dict[str, Any]: Dict con datos del usuario (id, display_name, email, country, followers, product).
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{SpotifyClient.BASE_URL}/me", headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_top_artists(token: str, limit: int = 50, offset: int = 0, time_range: str = "medium_term") -> Dict[str, Any]:
        """
        Obtiene top artistas del usuario.

        Args:
            token (str): Access token válido de Spotify.
            limit (int): Número de artistas (máx 50).
            offset (int): Offset para paginación.
            time_range (str): "short_term", "medium_term", o "long_term".

        Returns:
            Dict[str, Any]: Dict con items (artistas).
        """
        headers = {"Authorization": f"Bearer {token}"}
        params = {"limit": limit, "offset": offset, "time_range": time_range}
        response = requests.get(
            f"{SpotifyClient.BASE_URL}/me/top/artists",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_top_tracks(token: str, limit: int = 50, offset: int = 0, time_range: str = "medium_term") -> Dict[str, Any]:
        """
        Obtiene top canciones del usuario.

        Args:
            token (str): Access token válido de Spotify.
            limit (int): Número de canciones (máx 50).
            offset (int): Offset para paginación.
            time_range (str): "short_term", "medium_term", o "long_term".

        Returns:
            Dict[str, Any]: Dict con items (canciones).
        """
        headers = {"Authorization": f"Bearer {token}"}
        params = {"limit": limit, "offset": offset, "time_range": time_range}
        response = requests.get(
            f"{SpotifyClient.BASE_URL}/me/top/tracks",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_artists(token: str, artist_ids: list) -> list:
        """
        Obtiene datos completos de hasta 50 artistas por ID (incluye popularity real).
        Usa GET /v1/artists?ids=... que siempre retorna popularity independiente del modo.
        """
        headers = {"Authorization": f"Bearer {token}"}
        results = []
        for i in range(0, len(artist_ids), 50):
            batch = artist_ids[i:i + 50]
            response = requests.get(
                f"{SpotifyClient.BASE_URL}/artists",
                headers=headers,
                params={"ids": ",".join(batch)},
            )
            response.raise_for_status()
            results.extend(response.json().get("artists") or [])
        return results

    @staticmethod
    def get_tracks(token: str, track_ids: list) -> list:
        """
        Obtiene datos completos de hasta 50 canciones por ID (incluye album images).
        Usa GET /v1/tracks?ids=... compatible con Client Credentials token.
        """
        headers = {"Authorization": f"Bearer {token}"}
        results = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i + 50]
            response = requests.get(
                f"{SpotifyClient.BASE_URL}/tracks",
                headers=headers,
                params={"ids": ",".join(batch)},
            )
            response.raise_for_status()
            results.extend(response.json().get("tracks") or [])
        return results

    @staticmethod
    def get_artist(token: str, artist_id: str) -> Optional[Dict[str, Any]]:
        """GET /v1/artists/{id} — endpoint individual, a veces no bloqueado en Development Mode."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{SpotifyClient.BASE_URL}/artists/{artist_id}",
            headers=headers,
        )
        if response.status_code == 403:
            return None
        response.raise_for_status()
        return response.json()

    @staticmethod
    def search_track(token: str, track_name: str, artist_name: str = "") -> Optional[Dict[str, Any]]:
        """
        Busca una canción por nombre (+ artista opcional) y devuelve el primer resultado.
        Usa GET /v1/search?type=track — funciona en Development Mode.
        """
        headers = {"Authorization": f"Bearer {token}"}
        q = f"track:{track_name} artist:{artist_name}" if artist_name else track_name
        response = requests.get(
            f"{SpotifyClient.BASE_URL}/search",
            headers=headers,
            params={"q": q, "type": "track", "limit": 1},
        )
        response.raise_for_status()
        items = response.json().get("tracks", {}).get("items", [])
        return items[0] if items else None

    @staticmethod
    def search_artist(token: str, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Busca un artista por nombre y devuelve el primer resultado con todos sus campos.
        Usa GET /v1/search?type=artist — funciona en Development Mode sin restricciones.
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{SpotifyClient.BASE_URL}/search",
            headers=headers,
            params={"q": artist_name, "type": "artist", "limit": 1},
        )
        response.raise_for_status()
        items = response.json().get("artists", {}).get("items", [])
        return items[0] if items else None

    @staticmethod
    def get_recently_played(token: str, limit: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene historial de reproducción reciente.

        Args:
            token (str): Access token válido de Spotify.
            limit (int): Número de items (máx 50).
            after (str): Timestamp en ms para paginación hacia atrás.

        Returns:
            Dict[str, Any]: Dict con items (historial) y cursores.
        """
        headers = {"Authorization": f"Bearer {token}"}
        params = {"limit": limit}
        if after:
            params["after"] = after

        response = requests.get(
            f"{SpotifyClient.BASE_URL}/me/player/recently-played",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
