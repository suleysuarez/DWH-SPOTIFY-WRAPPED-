"""
filename: auth.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Schemas Pydantic para el flujo OAuth PKCE. Define AuthLoginResponse,
             AuthCallbackRequest y AuthCallbackResponse del módulo de autenticación.
"""

from pydantic import BaseModel


class AuthLoginResponse(BaseModel):
    """Response de GET /v1/auth/login."""
    authorization_url: str


class AuthCallbackRequest(BaseModel):
    """Request de GET /v1/auth/callback."""
    code: str
    state: str


class AuthCallbackResponse(BaseModel):
    """Response de GET /v1/auth/callback."""
    token: str
    token_type: str = "bearer"
