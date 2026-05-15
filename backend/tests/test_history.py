"""
filename: test_history.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Tests para EtlService.transform_history (unitarios) y los endpoints
             GET /v1/history/* (integración con mock de DB).
"""

import pytest
from datetime import datetime
from app.v1.services.etl_service import EtlService


# ─── Transform ────────────────────────────────────────────────────────────────

class TestTransformHistory:
    """Tests unitarios para EtlService.transform_history."""

    def _item_raw(self, track_id="t1", artist_id="a1",
                  played_at="2026-05-10T14:30:00Z", context_type="playlist"):
        return {
            "track": {"id": track_id, "artists": [{"id": artist_id}]},
            "played_at": played_at,
            "context": {"type": context_type} if context_type else None,
        }

    def test_transforma_campos_correctamente(self):
        raw = [self._item_raw("t1", "a1", "2026-05-10T14:30:00Z", "playlist")]
        result = EtlService.transform_history(raw)
        assert len(result) == 1
        item = result[0]
        assert item["spotify_track_id"] == "t1"
        assert item["spotify_artist_id"] == "a1"
        assert isinstance(item["played_at"], datetime)
        assert item["hour_of_day"] == 14
        assert item["day_of_week"] == "Sunday"
        assert item["context_type"] == "playlist"

    def test_sin_contexto_retorna_unknown(self):
        raw = [self._item_raw(context_type=None)]
        result = EtlService.transform_history(raw)
        assert result[0]["context_type"] == "unknown"

    def test_hour_of_day_refleja_hora_utc(self):
        raw = [self._item_raw(played_at="2026-05-10T08:15:00Z")]
        result = EtlService.transform_history(raw)
        assert result[0]["hour_of_day"] == 8

    def test_day_of_week_correcto(self):
        # 2026-05-11 es lunes (Monday)
        raw = [self._item_raw(played_at="2026-05-11T12:00:00Z")]
        result = EtlService.transform_history(raw)
        assert result[0]["day_of_week"] == "Monday"

    def test_played_at_como_datetime(self):
        raw = [self._item_raw()]
        result = EtlService.transform_history(raw)
        assert isinstance(result[0]["played_at"], datetime)

    def test_lista_vacia_retorna_vacia(self):
        assert EtlService.transform_history([]) == []

    def test_multiples_items_preservan_orden(self):
        raw = [self._item_raw(track_id=f"t{i}", played_at=f"2026-05-10T{10+i:02d}:00:00Z") for i in range(3)]
        result = EtlService.transform_history(raw)
        assert len(result) == 3
        for i, item in enumerate(result):
            assert item["spotify_track_id"] == f"t{i}"


# ─── Endpoints ────────────────────────────────────────────────────────────────

class TestRecentlyPlayedEndpoint:
    """Tests para GET /v1/history/recently-played."""

    def test_sin_autenticacion_retorna_403(self, test_client):
        response = test_client.get("/v1/history/recently-played")
        assert response.status_code == 403

    def test_token_invalido_retorna_401(self, test_client):
        response = test_client.get(
            "/v1/history/recently-played",
            headers={"Authorization": "Bearer bad_token"},
        )
        assert response.status_code == 401

    def test_con_token_valido_retorna_200(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/recently-played",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    def test_respuesta_tiene_shape_correcto(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/recently-played",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_sin_datos_retorna_lista_vacia(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/recently-played",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestHistoryStatsEndpoint:
    """Tests para GET /v1/history/stats."""

    def test_con_token_valido_retorna_200(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/stats",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    def test_shape_tiene_campos_requeridos(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/stats",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        for campo in ("total_tracks", "total_artists", "total_plays", "total_minutes"):
            assert campo in data, f"Campo '{campo}' ausente"

    def test_sin_datos_retorna_ceros(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/stats",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert data["total_tracks"] == 0
        assert data["total_plays"] == 0


class TestGenresEndpoint:
    """Tests para GET /v1/history/genres."""

    def test_con_token_valido_retorna_200(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/genres",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    def test_respuesta_contiene_genres_y_total(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/genres",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert "genres" in data
        assert "total_plays" in data
        assert isinstance(data["genres"], list)


class TestPeakHourEndpoint:
    """Tests para GET /v1/history/peak-hour."""

    def test_con_token_valido_retorna_200(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/peak-hour",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    def test_sin_datos_retorna_hora_cero(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/peak-hour",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert data["hour"] == 0
        assert data["play_count"] == 0
        assert "label" in data

    def test_distribucion_retorna_24_horas(self, test_client, valid_token):
        response = test_client.get(
            "/v1/history/peak-hour/distribution",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["hours"]) == 24
