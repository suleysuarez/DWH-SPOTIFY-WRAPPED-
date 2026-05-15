"""
auth.py (LEGACY — app/routers/) — Rutas de autenticación OAuth PKCE.

⚠️  ARCHIVO LEGACY: Este router NO está montado en la aplicación activa.
    El router equivalente activo es app/v1/routers/auth.py.

Diferencias con la versión activa (v1):
- El callback aquí es POST con body JSON; en v1 es GET con query params.
- Usa `core/security.py` en lugar de `v1/services/auth_service.py`.
- La sesión PKCE tiene campos adicionales (code_challenge, expires_at, used).

Se conserva como referencia histórica del diseño original.
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    generate_pkce_pair, generate_state, create_jwt_token, verify_jwt_token
)
from app.models.models import PkceSessions, DimUsers
from app.schemas.schemas import AuthLoginResponse, AuthCallbackRequest, AuthCallbackResponse
from app.services.spotify_service import SpotifyService
from app.services.etl_service import EtlService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/login", response_model=AuthLoginResponse)
def login(db: Session = Depends(get_db)):
    """
    Inicia flujo OAuth PKCE.
    
    Retorna URL de autorización de Spotify.
    El frontend debe redirigir a esta URL con window.location.href (NO fetch).
    """
    logger.info("Iniciando flujo OAuth PKCE...")
    
    # Generar PKCE pair y state
    code_verifier, code_challenge = generate_pkce_pair()
    state = generate_state()
    
    # Guardar en DB para verificación posterior
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    pkce_session = PkceSessions(
        state=state,
        code_verifier=code_verifier,
        code_challenge=code_challenge,
        expires_at=expires_at,
    )
    db.add(pkce_session)
    db.commit()
    
    logger.info(f"PKCE session creada: state={state}")
    
    # Construir URL de autorización
    authorization_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={settings.SPOTIFY_CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={settings.SPOTIFY_REDIRECT_URI}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256&"
        f"state={state}&"
        f"scope=user-read-private user-read-email user-top-read user-read-recently-played"
    )
    
    return AuthLoginResponse(authorization_url=authorization_url)


@router.post("/callback", response_model=AuthCallbackResponse)
def callback(request: AuthCallbackRequest, db: Session = Depends(get_db)):
    """
    Callback de Spotify OAuth.
    
    Recibe: code, state
    Retorna: JWT para guardar en localStorage
    """
    logger.info(f"Callback recibido: state={request.state}")
    
    # Verificar state y obtener code_verifier
    pkce_session = db.query(PkceSessions).filter_by(state=request.state).first()
    
    if not pkce_session:
        logger.error(f"State no encontrado: {request.state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido o expirado",
        )
    
    if pkce_session.used:
        logger.error(f"State ya fue usado: {request.state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State ya fue utilizado",
        )
    
    if datetime.utcnow() > pkce_session.expires_at:
        logger.error(f"State expirado: {request.state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State expirado",
        )
    
    # Marcar como usado
    pkce_session.used = True
    db.commit()
    
    # Intercambiar code por token
    try:
        token_response = SpotifyService.get_access_token(request.code, pkce_session.code_verifier)
        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        
        logger.info("Access token obtenido de Spotify")
    except Exception as e:
        logger.error(f"Error intercambiando code: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error obteniendo token de Spotify",
        )
    
    # Obtener datos del usuario
    try:
        user_data = EtlService.extract_user(access_token)
        transformed_user = EtlService.transform_user(user_data)
        user_id = EtlService.load_user(db, transformed_user, access_token, refresh_token)
        
        logger.info(f"Usuario cargado/actualizado: user_id={user_id}")
    except Exception as e:
        logger.error(f"Error cargando usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando datos del usuario",
        )
    
    # Crear JWT
    jwt_token = create_jwt_token(user_id, user_data["id"])
    
    logger.info(f"JWT creado para user_id={user_id}")
    
    return AuthCallbackResponse(access_token=jwt_token)
