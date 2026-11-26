"""
filename: test_wrapped_exchange.py
description: Pruebas de GET /v1/history/wrapped y del intercambio de código por JWT.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace

from app.v1.services.auth_service import AuthService

CODE = "c" * 43


def _exchange_row(mock_db, row):
    mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = row


def test_wrapped_requiere_jwt(test_client):
    assert test_client.get("/v1/history/wrapped").status_code in (401, 403)


def test_wrapped_sin_datos(test_client, valid_token):
    res = test_client.get("/v1/history/wrapped", headers={"Authorization": f"Bearer {valid_token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["total_plays"] == 0
    assert body["total_minutes"] == 0
    assert body["top_artist"] is None
    assert body["top_track"] is None
    assert body["peak_hour"] is None


def test_exchange_entrega_jwt_y_consume_el_codigo(test_client, mock_db):
    row = SimpleNamespace(verifier="test_spotify_id", created_at=datetime.utcnow())
    _exchange_row(mock_db, row)
    res = test_client.post("/v1/auth/exchange", json={"code": CODE})
    assert res.status_code == 200
    assert AuthService.verify_jwt_token(res.json()["token"])["sub"] == "test_spotify_id"
    mock_db.delete.assert_called_once_with(row)


def test_exchange_codigo_inexistente(test_client, mock_db):
    _exchange_row(mock_db, None)
    assert test_client.post("/v1/auth/exchange", json={"code": CODE}).status_code == 400


def test_exchange_codigo_expirado(test_client, mock_db):
    row = SimpleNamespace(verifier="test_spotify_id", created_at=datetime.utcnow() - timedelta(minutes=5))
    _exchange_row(mock_db, row)
    assert test_client.post("/v1/auth/exchange", json={"code": CODE}).status_code == 400
    mock_db.delete.assert_called_once_with(row)
