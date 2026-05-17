"""
filename: conftest.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Fixtures compartidos para pytest. Configura variables de entorno de prueba,
             mock de la sesión SQLAlchemy y TestClient de FastAPI con dependencias sobrescritas.
"""

import os

# Variables de entorno deben estar antes de cualquier import de la app
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test_client_id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test_client_secret")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_key_32chars_long!")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("ALLOW_HOSTS", "http://localhost:3000")

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.v1.services.auth_service import AuthService


class FakeUser:
    """Objeto usuario simulado que replica la interfaz de DimUsers para tests."""

    user_id = 1
    spotify_id = "test_spotify_id"
    display_name = "Test User"
    email = "test@example.com"
    country = "CO"
    followers = 100
    product = "free"
    image_url = "https://example.com/photo.jpg"
    spotify_access_token = "mock_access_token"
    spotify_refresh_token = "mock_refresh_token"
    token_expires_at = None
    loaded_at = datetime(2026, 5, 15, 12, 0, 0)


@pytest.fixture
def fake_user():
    """Retorna una instancia de usuario simulado."""
    return FakeUser()


@pytest.fixture
def valid_token():
    """JWT válido firmado para el usuario de prueba (test_spotify_id)."""
    return AuthService.create_jwt_token("test_spotify_id")


@pytest.fixture
def mock_db(fake_user):
    """
    Sesión SQLAlchemy simulada con encadenamiento fluido.

    join/filter/group_by/order_by/limit/offset devuelven el mismo mock para permitir
    cadenas arbitrarias. filter_by tiene su propio mock con valores específicos.
    """
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q

    # Encadenamiento fluido: todos vuelven al mismo mock
    q.join.return_value = q
    q.filter.return_value = q
    q.group_by.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.offset.return_value = q

    # Terminadores del mock principal
    q.all.return_value = []
    q.scalar.return_value = 0
    q.first.return_value = None
    q.count.return_value = 0

    # filter_by genera su propio mock con valores para auth y conteos
    fb = MagicMock()
    q.filter_by.return_value = fb
    fb.first.return_value = fake_user     # autenticación JWT → DimUsers
    fb.scalar.return_value = 0
    fb.count.return_value = 0
    fb.order_by.return_value.limit.return_value.all.return_value = []
    fb.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

    return db


@pytest.fixture
def test_client(mock_db):
    """TestClient de FastAPI con get_db sobrescrito por mock_db."""
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()
