"""
filename: auth.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Router de autenticación OAuth 2.0 PKCE con Spotify. GET /v1/auth/login genera
             el par PKCE y retorna la URL de autorización. GET /v1/auth/callback intercambia
             el code por tokens de Spotify, carga el usuario en el DWH y emite el JWT de la app.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.models import PkceSessions
from app.schemas.schemas import AuthLoginResponse
from app.services.spotify_service import SpotifyService
from app.services.etl_service import EtlService
from app.v1.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_model=AuthLoginResponse)
def login(db: Session = Depends(get_db)):
    """
    Inicia flujo OAuth PKCE.
    Retorna URL de autorización de Spotify.
    El frontend hace fetch y luego redirige con window.location.href.
    """
    logger.info("Iniciando flujo OAuth PKCE...")

    code_verifier, code_challenge = AuthService.generate_pkce_pair()
    state = AuthService.generate_state()

    pkce_session = PkceSessions(
        state=state,
        verifier=code_verifier,
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


@router.get("/callback")
def callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Callback de Spotify OAuth.
    Recibe code y state como query params (GET).
    Redirige al frontend con el JWT como query param.
    """
    logger.info(f"Callback recibido: state={state}")

    pkce_session = db.query(PkceSessions).filter_by(state=state).first()

    if not pkce_session:
        logger.error(f"State no encontrado: {state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido o expirado",
        )

    code_verifier = pkce_session.verifier
    db.delete(pkce_session)
    db.commit()

    # Intercambiar code por token de Spotify
    try:
        token_response = SpotifyService.get_access_token(code, code_verifier)
        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        logger.info("Access token obtenido de Spotify")
    except Exception as e:
        logger.error(f"Error intercambiando code: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error obteniendo token de Spotify",
        )

    # ETL: extraer, transformar y cargar usuario
    try:
        user_data = EtlService.extract_user(access_token)
        transformed_user = EtlService.transform_user(user_data)
        EtlService.load_user(db, transformed_user, access_token, refresh_token)
        spotify_id = user_data["id"]
        logger.info(f"Usuario cargado/actualizado: {spotify_id}")
    except Exception as e:
        logger.error(f"Error cargando usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando datos del usuario",
        )

    # Crear JWT usando AuthService (compatible con verify_jwt_token en todos los routers)
    jwt_token = AuthService.create_jwt_token(spotify_id)
    logger.info(f"JWT creado para spotify_id={spotify_id}")

    # Redirigir al frontend con el token
    frontend_url = settings.FRONTEND_URL
    return RedirectResponse(url=f"{frontend_url}/callback?token={jwt_token}")