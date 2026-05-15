"""
filename: auth_service.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Servicio de autenticación OAuth PKCE y JWT. Genera par PKCE (verifier/challenge S256),
             state CSRF y tokens JWT HS256 con expiración de 8h para proteger los endpoints.
"""

import jwt
import secrets
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from typing import Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Servicio de autenticación."""

    @staticmethod
    def generate_pkce_pair() -> Tuple[str, str]:
        """
        Genera code_verifier y code_challenge para PKCE.

        Returns:
            Tuple[str, str]: (code_verifier, code_challenge).
        """
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode("utf-8").rstrip("=")
        return code_verifier, code_challenge

    @staticmethod
    def generate_state() -> str:
        """
        Genera un state único para PKCE.

        Returns:
            str: State aleatorio.
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_jwt_token(spotify_id: str) -> str:
        """
        Crea un JWT con expiración de 8 horas.

        Args:
            spotify_id (str): ID de Spotify del usuario.

        Returns:
            str: Token JWT firmado.
        """
        now = datetime.utcnow()
        payload = {
            "sub": spotify_id,
            "iat": now,
            "exp": now + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def verify_jwt_token(token: str) -> dict:
        """
        Verifica y decodifica un JWT.

        Args:
            token (str): Token JWT a verificar.

        Returns:
            dict: Payload del token.

        Raises:
            jwt.ExpiredSignatureError: Si el token expiró.
            jwt.InvalidTokenError: Si el token es inválido.
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.error("Token expirado")
            raise
        except jwt.InvalidTokenError:
            logger.error("Token inválido")
            raise
