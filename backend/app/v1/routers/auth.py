"""
filename: auth.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Router de autenticación OAuth 2.0 PKCE con Spotify. GET /v1/auth/login genera
             el par PKCE y retorna la URL de autorización. GET /v1/auth/callback intercambia
             el code por tokens de Spotify, carga el usuario en el DWH y entrega al frontend un
             código de un solo uso que POST /v1/auth/exchange cambia por el JWT de la app.
"""
import logging
import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.models import PkceSessions
from app.schemas.schemas import AuthLoginResponse
from app.services.spotify_service import SpotifyService
from app.v1.services.etl_service import EtlService
from app.v1.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Los códigos de intercambio se guardan en pkce_sessions con este prefijo.
# Un state de PKCE (token_urlsafe) nunca contiene ":", así que no se confunden.
EXCHANGE_PREFIX = "xc:"
EXCHANGE_TTL_SECONDS = 60


class TokenExchangeRequest(BaseModel):
    code: str = Field(min_length=20, max_length=100)


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
    Redirige al frontend con un código de un solo uso (nunca con el JWT).
    """
    logger.info(f"Callback recibido: state={state}")

    pkce_session = None if ":" in state else db.query(PkceSessions).filter_by(state=state).first()

    if not pkce_session:
        logger.error(f"State no encontrado: {state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido o expirado",
        )

    code_verifier = pkce_session.verifier

    # Intercambiar code por token de Spotify
    try:
        token_response = SpotifyService.get_access_token(code, code_verifier)
        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        logger.info("Access token obtenido de Spotify")
    except Exception as e:
        logger.error(f"Error intercambiando code: {e}")
        # No eliminar la sesión PKCE — el code ya fue consumido por Spotify,
        # así que el state no puede reutilizarse de todos modos.
        db.delete(pkce_session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error obteniendo token de Spotify",
        )

    # El code ya fue usado; eliminar la sesión PKCE ahora que tenemos el token.
    db.delete(pkce_session)
    db.commit()

    # ETL: extraer, transformar y cargar usuario
    try:
        user_data = EtlService.extract_user(access_token)
        transformed_user = EtlService.transform_user(user_data)
        EtlService.load_user(db, transformed_user, access_token, refresh_token)
        spotify_id = user_data["id"]
        logger.info(f"Usuario cargado/actualizado: {spotify_id}")
    except Exception as e:
        logger.error(f"Error cargando usuario: {e}")
        # 403 = usuario no registrado como test user en Spotify Developer Dashboard
        detail = "Usuario no autorizado en la aplicación de Spotify" if "403" in str(e) else "Error procesando datos del usuario"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "403" in str(e) else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )

    # El JWT no viaja en la URL: se entrega un código de un solo uso y corta duración.
    exchange_code = secrets.token_urlsafe(32)
    db.add(PkceSessions(
        state=EXCHANGE_PREFIX + exchange_code,
        verifier=spotify_id,
        created_at=datetime.utcnow(),
    ))
    db.commit()

    # Redirigir al frontend con el código
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/callback?code={exchange_code}")


@router.post("/exchange")
def exchange(body: TokenExchangeRequest, db: Session = Depends(get_db)):
    """
    Cambia el código de un solo uso por el JWT de la aplicación.

    El código se elimina al primer uso y caduca a los 60 segundos.
    """
    row = db.query(PkceSessions).filter(
        PkceSessions.state == EXCHANGE_PREFIX + body.code
    ).with_for_update().first()

    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Código inválido o expirado",
    )
    if not row:
        raise invalid

    spotify_id, created_at = row.verifier, row.created_at
    db.delete(row)
    db.commit()

    if created_at is None or datetime.utcnow() - created_at > timedelta(seconds=EXCHANGE_TTL_SECONDS):
        raise invalid

    logger.info(f"JWT creado para spotify_id={spotify_id}")
    return {"token": AuthService.create_jwt_token(spotify_id)}
