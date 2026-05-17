"""
security.py — Utilidades de seguridad: JWT y PKCE.

NOTA: Este módulo pertenece al flujo LEGACY (app/routers/). El flujo activo
usa `app/v1/services/auth_service.py` (clase AuthService) que reimplementa
las mismas operaciones. Ambos leen la misma configuración de `settings`.

Expone funciones de bajo nivel para:
- Generación de tokens PKCE (code_verifier / code_challenge S256).
- Creación y verificación de JWT firmados con HS256.
- Extracción del Bearer token del header Authorization.
"""

import jwt
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from app.core.config import settings


def create_jwt_token(user_id: int, spotify_id: str) -> str:
    """
    Crea un JWT con expiración de 8 horas.
    
    Args:
        user_id: ID interno del usuario
        spotify_id: ID de Spotify del usuario
        
    Returns:
        Token JWT firmado
    """
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "spotify_id": spotify_id,
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """
    Verifica y decodifica un JWT.
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        Payload del token
        
    Raises:
        HTTPException si el token es inválido o expiró
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )


def generate_pkce_pair() -> tuple[str, str]:
    """
    Genera code_verifier y code_challenge para PKCE.
    
    Returns:
        (code_verifier, code_challenge)
    """
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


def generate_state() -> str:
    """Genera un state único para PKCE."""
    return secrets.token_urlsafe(32)


def extract_bearer_token(auth_header: Optional[str]) -> str:
    """
    Extrae el token del header Authorization: Bearer <token>.
    
    Args:
        auth_header: Valor del header Authorization
        
    Returns:
        Token extraído
        
    Raises:
        HTTPException si el header es inválido
    """
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header faltante",
        )
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header inválido",
        )
    
    return parts[1]
