"""
filename: test_tracks.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Tests para EtlService.transform_tracks (unitarios) y GET /v1/tracks/top
             (integración con mock de DB). Verifica normalización y autenticación.
"""

import pytest
from app.v1.services.etl_service import EtlService


# ─── Transform ────────────────────────────────────────────────────────────────

class TestTransformTracks:
    """Tests unitarios para EtlService.transform_tracks."""

    def _track_raw(self, track_id="t1", name="Track", artist_id="a1",
                   artist_name="Artista", album="Album", duration=180_000,
                   popularity=80, explicit=False, album_image=None):
        imagenes = [{"url": album_image}] if album_image else []
        return {
            "id": track_id,
            "name": name,
            "artists": [{"id": artist_id, "name": artist_name}],
            "album": {"name": album, "images": imagenes},
            "duration_ms": duration,
            "popularity": popularity,
            "explicit": explicit,
        }

    def test_transforma_campos_obligatorios(self):
        raw = [self._track_raw("t1", "BICHOTA", "a1", "Karol G",
                               "KG0516", 210_000, 85, False, "https://img.com/album.jpg")]
        result = EtlService.transform_tracks(raw)
        assert len(result) == 1
        t = result[0]
        assert t["spotify_id"] == "t1"
        assert t["name"] == "BICHOTA"
        assert t["spotify_artist_id"] == "a1"
        assert t["artist_name"] == "Karol G"
        assert t["album_name"] == "KG0516"
        assert t["duration_ms"] == 210_000
        assert t["popularity"] == 85
        assert t["explicit"] is False
        assert t["album_image_url"] == "https://img.com/album.jpg"

    def test_album_sin_imagenes_retorna_album_image_url_none(self):
        raw = [self._track_raw(album_image=None)]
        result = EtlService.transform_tracks(raw)
        assert result[0]["album_image_url"] is None

    def test_explicit_true_se_preserva(self):
        raw = [self._track_raw(explicit=True)]
        result = EtlService.transform_tracks(raw)
        assert result[0]["explicit"] is True

    def test_lista_vacia_retorna_vacia(self):
        assert EtlService.transform_tracks([]) == []

    def test_multiples_tracks_preservan_orden(self):
        raw = [self._track_raw(track_id=f"t{i}", name=f"Track {i}") for i in range(3)]
        result = EtlService.transform_tracks(raw)
        assert len(result) == 3
        for i, item in enumerate(result):
            assert item["spotify_id"] == f"t{i}"


# ─── Endpoint ─────────────────────────────────────────────────────────────────

class TestTopTracksEndpoint:
    """Tests de integración para GET /v1/tracks/top."""

    def test_sin_autenticacion_retorna_403(self, test_client):
        response = test_client.get("/v1/tracks/top")
        assert response.status_code == 403

    def test_token_invalido_retorna_401(self, test_client):
        response = test_client.get(
            "/v1/tracks/top",
            headers={"Authorization": "Bearer token_invalido"},
        )
        assert response.status_code == 401

    def test_con_token_valido_retorna_200(self, test_client, valid_token):
        response = test_client.get(
            "/v1/tracks/top",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    def test_respuesta_tiene_shape_correcto(self, test_client, valid_token):
        response = test_client.get(
            "/v1/tracks/top",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert "tracks" in data
        assert "total" in data
        assert isinstance(data["tracks"], list)
        assert isinstance(data["total"], int)

    def test_sin_datos_retorna_lista_vacia(self, test_client, valid_token):
        response = test_client.get(
            "/v1/tracks/top",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert data["total"] == 0
        assert data["tracks"] == []
