"""
filename: auth.py
author: Suley & Jhonatan
date: 2026-05-12
version: 1.0
description: Schemas Pydantic para autenticación OAuth PKCE y JWT.
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
