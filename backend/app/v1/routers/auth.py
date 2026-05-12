"""
filename: auth.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Rutas de autenticación OAuth PKCE. Endpoints: GET /v1/auth/login, GET /v1/auth/callback.
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.models import PkceSessions, DimUsers
from app.v1.schemas.auth import AuthLoginResponse, AuthCallbackRequest, AuthCallbackResponse
from app.v1.services.auth_service import AuthService
from app.v1.services.spotify_client import SpotifyClient
from app.v1.services.etl_service import EtlService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_model=AuthLoginResponse)
def login(db: Session = Depends(get_db)):
    """
    Inicia flujo OAuth PKCE.

    Retorna URL de autorización de Spotify.
    El frontend debe redirigir a esta URL con window.location.href.
    """
    logger.info("Iniciando flujo OAuth PKCE...")
    
    code_verifier, code_challenge = AuthService.generate_pkce_pair()
    state = AuthService.generate_state()
    
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    pkce_session = PkceSessions(
        state=state,
        verifier=code_verifier,
        created_at=datetime.utcnow(),
    )
    db.add(pkce_session)
    db.commit()
    
    logger.info(f"PKCE session creada: state={state}")
    
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


@router.get("/callback", response_model=AuthCallbackResponse)
def callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Callback de Spotify OAuth.

    Recibe: code, state
    Retorna: JWT para guardar en localStorage
    """
    logger.info(f"Callback recibido: state={state}")
    
    pkce_session = db.query(PkceSessions).filter_by(state=state).first()
    
    if not pkce_session:
        logger.error(f"State no encontrado: {state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido o expirado",
        )
    
    if datetime.utcnow() > pkce_session.created_at + timedelta(minutes=10):
        logger.error(f"State expirado: {state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State expirado",
        )
    
    try:
        token_response = SpotifyClient.get_access_token(
            code,
            pkce_session.verifier,
            settings.SPOTIFY_CLIENT_ID,
            settings.SPOTIFY_CLIENT_SECRET,
            settings.SPOTIFY_REDIRECT_URI,
        )
        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        
        logger.info("Access token obtenido de Spotify")
    except Exception as e:
        logger.error(f"Error intercambiando code: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error obteniendo token de Spotify",
        )
    
    try:
        user_data = EtlService.extract_user(access_token)
        transformed_user = EtlService.transform_user(user_data)
        spotify_id = EtlService.load_user(db, transformed_user, access_token, refresh_token)
        
        logger.info(f"Usuario cargado: {spotify_id}")
    except Exception as e:
        logger.error(f"Error cargando usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando datos del usuario",
        )
    
    jwt_token = AuthService.create_jwt_token(spotify_id)
    
    logger.info(f"JWT creado para {spotify_id}")
    
    # Limpiar PKCE session
    db.delete(pkce_session)
    db.commit()
    
    return AuthCallbackResponse(token=jwt_token)
