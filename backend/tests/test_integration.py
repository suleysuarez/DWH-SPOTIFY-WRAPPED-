"""
filename: test_integration.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Tests de integración para el pipeline ETL, endpoint de status y circuit breaker.
             Usa TestClient con mocks de DB y servicios externos para simular flujos completos.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState
from app.v1.services.auth_service import AuthService


# ── Helpers ───────────────────────────────────────────────────────────────────

def auth_headers(spotify_id: str = "test_spotify_id") -> dict:
    token = AuthService.create_jwt_token(spotify_id)
    return {"Authorization": f"Bearer {token}"}


def make_fake_audit(
    audit_id=1,
    status="success",
    started_at=None,
    finished_at=None,
    duration_ms=5000,
    artists_new=10,
    tracks_new=20,
    history_new=5,
    artists_skipped=0,
    tracks_skipped=0,
    history_skipped=0,
    cursor_after_ms=None,
    cursor_next_ms=None,
    error_message=None,
):
    audit = MagicMock()
    audit.audit_id = audit_id
    audit.status = status
    audit.started_at = started_at or datetime(2026, 5, 15, 12, 0, 0)
    audit.finished_at = finished_at or datetime(2026, 5, 15, 12, 0, 5)
    audit.duration_ms = duration_ms
    audit.artists_new = artists_new
    audit.tracks_new = tracks_new
    audit.history_new = history_new
    audit.artists_skipped = artists_skipped
    audit.tracks_skipped = tracks_skipped
    audit.history_skipped = history_skipped
    audit.cursor_after_ms = cursor_after_ms
    audit.cursor_next_ms = cursor_next_ms
    audit.error_message = error_message
    return audit


# ── Fixtures ──────────────────────────────────────────────────────────────────

class FakeUser:
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


@pytest.fixture
def fake_user():
    return FakeUser()


@pytest.fixture
def mock_db(fake_user):
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.join.return_value = q
    q.filter.return_value = q
    q.group_by.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.offset.return_value = q
    q.all.return_value = []
    q.scalar.return_value = 0
    q.first.return_value = None
    q.count.return_value = 0
    fb = MagicMock()
    q.filter_by.return_value = fb
    fb.first.return_value = fake_user
    fb.scalar.return_value = 0
    fb.count.return_value = 0
    fb.order_by.return_value.limit.return_value.all.return_value = []
    fb.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    return db


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    app.dependency_overrides.clear()


# ── Tests: GET /v1/etl/status ─────────────────────────────────────────────────

class TestEtlStatus:

    def test_status_returns_three_tables(self, client):
        """El endpoint debe retornar exactamente 3 tablas del DWH."""
        resp = client.get("/v1/etl/status", headers=auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "tables" in data
        assert len(data["tables"]) == 3

    def test_status_table_names(self, client):
        """Las tablas deben ser dim_artists, dim_tracks y fact_listening_history."""
        resp = client.get("/v1/etl/status", headers=auth_headers())
        names = [t["table_name"] for t in resp.json()["tables"]]
        assert "dim_artists" in names
        assert "dim_tracks" in names
        assert "fact_listening_history" in names

    def test_status_last_sync_populated(self, client, mock_db):
        """last_sync debe aparecer cuando existe un audit exitoso con finished_at."""
        fake_audit = make_fake_audit(
            finished_at=datetime(2026, 5, 20, 10, 0, 0)
        )
        fb = mock_db.query.return_value.filter_by.return_value
        fb.order_by.return_value.first.return_value = fake_audit

        resp = client.get("/v1/etl/status", headers=auth_headers())
        assert resp.status_code == 200
        for table in resp.json()["tables"]:
            assert table["last_sync"] is not None
            assert "2026-05-20" in table["last_sync"]

    def test_status_last_sync_null_when_no_audit(self, client, mock_db):
        """last_sync debe ser null cuando no hay audits exitosos."""
        fb = mock_db.query.return_value.filter_by.return_value
        fb.order_by.return_value.first.return_value = None

        resp = client.get("/v1/etl/status", headers=auth_headers())
        assert resp.status_code == 200
        for table in resp.json()["tables"]:
            assert table["last_sync"] is None

    def test_status_requires_auth(self, client):
        """Sin JWT debe retornar 403."""
        resp = client.get("/v1/etl/status")
        assert resp.status_code == 403

    def test_status_recent_runs_present(self, client, mock_db):
        """recent_runs debe estar en la respuesta."""
        resp = client.get("/v1/etl/status", headers=auth_headers())
        assert "recent_runs" in resp.json()


# ── Tests: POST /v1/etl/run ───────────────────────────────────────────────────

class TestEtlRun:

    @patch("app.v1.routers.etl.EtlService")
    @patch("app.v1.routers.etl.SpotifyClient")
    def test_run_etl_success(self, mock_spotify, mock_etl, client, mock_db):
        """El ETL completo debe retornar status success."""
        mock_spotify.refresh_access_token.return_value = {"access_token": "new_token"}
        mock_etl.extract_user.return_value = {"id": "test_spotify_id", "display_name": "Test"}
        mock_etl.extract_top_artists.return_value = []
        mock_etl.extract_top_tracks.return_value = []
        mock_etl.extract_recently_played.return_value = ([], None)
        mock_etl.transform_user.return_value = {}
        mock_etl.transform_artists.return_value = []
        mock_etl.transform_tracks.return_value = []
        mock_etl.transform_history.return_value = []
        mock_etl.load_user.return_value = "test_spotify_id"
        mock_etl.load_artists.return_value = (0, 0)
        mock_etl.load_tracks.return_value = (0, 0)
        mock_etl.load_history.return_value = (0, 0)
        mock_etl.backfill_artist_genres.return_value = 0
        mock_etl.backfill_artist_stats.return_value = 0

        fb = mock_db.query.return_value.filter_by.return_value
        fb.order_by.return_value.first.return_value = None

        resp = client.post("/v1/etl/run", headers=auth_headers())
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    @patch("app.v1.routers.etl.EtlService")
    @patch("app.v1.routers.etl.SpotifyClient")
    def test_run_etl_logs_present(self, mock_spotify, mock_etl, client, mock_db):
        """La respuesta debe incluir logs del proceso."""
        mock_spotify.refresh_access_token.return_value = {"access_token": "new_token"}
        mock_etl.extract_user.return_value = {"id": "test_spotify_id"}
        mock_etl.extract_top_artists.return_value = []
        mock_etl.extract_top_tracks.return_value = []
        mock_etl.extract_recently_played.return_value = ([], None)
        mock_etl.transform_user.return_value = {}
        mock_etl.transform_artists.return_value = []
        mock_etl.transform_tracks.return_value = []
        mock_etl.transform_history.return_value = []
        mock_etl.load_user.return_value = "test_spotify_id"
        mock_etl.load_artists.return_value = (0, 0)
        mock_etl.load_tracks.return_value = (0, 0)
        mock_etl.load_history.return_value = (0, 0)
        mock_etl.backfill_artist_genres.return_value = 0
        mock_etl.backfill_artist_stats.return_value = 0

        fb = mock_db.query.return_value.filter_by.return_value
        fb.order_by.return_value.first.return_value = None

        resp = client.post("/v1/etl/run", headers=auth_headers())
        assert "logs" in resp.json()
        assert len(resp.json()["logs"]) > 0

    @patch("app.v1.routers.etl.EtlService")
    @patch("app.v1.routers.etl.SpotifyClient")
    def test_run_etl_error_returns_error_status(self, mock_spotify, mock_etl, client, mock_db):
        """Si el ETL falla, debe retornar status error sin lanzar excepción HTTP."""
        mock_spotify.refresh_access_token.return_value = {"access_token": "new_token"}
        mock_etl.extract_user.side_effect = Exception("Spotify API error")

        fb = mock_db.query.return_value.filter_by.return_value
        fb.order_by.return_value.first.return_value = None

        resp = client.post("/v1/etl/run", headers=auth_headers())
        assert resp.status_code == 200
        assert resp.json()["status"] == "error"

    def test_run_etl_requires_auth(self, client):
        """Sin JWT debe retornar 403."""
        resp = client.post("/v1/etl/run")
        assert resp.status_code == 403


# ── Tests: Circuit Breaker ────────────────────────────────────────────────────

class TestCircuitBreaker:

    def test_circuit_starts_closed(self):
        """El circuito debe iniciar en estado CLOSED."""
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
        assert cb.state == CircuitState.CLOSED

    def test_circuit_opens_after_threshold(self):
        """El circuito debe abrirse después de alcanzar el umbral de fallos."""
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)

        def failing_func():
            raise Exception("fallo")

        for _ in range(3):
            try:
                cb.call(failing_func)
            except Exception:
                pass

        assert cb.state == CircuitState.OPEN

    def test_circuit_open_raises_circuit_breaker_error(self):
        """Cuando el circuito está abierto debe lanzar CircuitBreakerError."""
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)

        def failing_func():
            raise Exception("fallo")

        try:
            cb.call(failing_func)
        except Exception:
            pass

        with pytest.raises(CircuitBreakerError):
            cb.call(lambda: "ok")

    def test_circuit_resets_on_success(self):
        """El circuito debe volver a CLOSED después de una llamada exitosa."""
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=60)
        cb.call(lambda: "ok")
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_circuit_half_open_after_timeout(self):
        """El circuito debe pasar a HALF_OPEN después del recovery_timeout."""
        import time
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=1)

        def failing_func():
            raise Exception("fallo")

        try:
            cb.call(failing_func)
        except Exception:
            pass

        assert cb._state == CircuitState.OPEN
        time.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN

    def test_get_status_returns_dict(self):
        """get_status debe retornar un dict con los campos esperados."""
        cb = CircuitBreaker(name="lastfm", failure_threshold=5, recovery_timeout=60)
        status = cb.get_status()
        assert status["name"] == "lastfm"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["failure_threshold"] == 5


# ── Tests: Rate Limiting ──────────────────────────────────────────────────────

class TestRateLimiting:

    def test_rate_limit_blocks_after_max_requests(self, client):
        """Debe retornar 429 después de exceder el límite de requests."""
        # Hacer más requests que el límite configurado
        responses = []
        for _ in range(105):
            resp = client.get("/health")
            responses.append(resp.status_code)

        assert 429 in responses

    def test_health_endpoint_accessible(self, client):
        """El endpoint /health debe ser accesible."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_circuit_breakers_endpoint(self, client):
        """El endpoint /circuit-breakers debe retornar el estado de los breakers."""
        resp = client.get("/circuit-breakers")
        assert resp.status_code == 200
        data = resp.json()
        assert "circuit_breakers" in data
        assert len(data["circuit_breakers"]) == 2
        names = [cb["name"] for cb in data["circuit_breakers"]]
        assert "lastfm" in names
        assert "spotify" in names
