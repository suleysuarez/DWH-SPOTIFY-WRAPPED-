"""
filename: test_artists.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Tests para EtlService.transform_artists (unitarios) y GET /v1/artists/top
             (integración con mock de DB). Verifica normalización de datos y autenticación.
"""

import pytest
from app.v1.services.etl_service import EtlService


# ─── Transform ────────────────────────────────────────────────────────────────

class TestTransformArtists:
    """Tests unitarios para EtlService.transform_artists."""

    def _artista_raw(self, artist_id="a1", name="Artista", popularity=80,
                     followers=1000, genres=None, image_url=None):
        imagenes = [{"url": image_url}] if image_url else []
        return {
            "id": artist_id,
            "name": name,
            "popularity": popularity,
            "followers": {"total": followers},
            "genres": genres or [],
            "images": imagenes,
        }

    def test_transforma_campos_obligatorios(self):
        raw = [self._artista_raw("a1", "Karol G", 90, 5_000_000,
                                 ["reggaeton", "latin pop"], "https://img.com/kg.jpg")]
        result = EtlService.transform_artists(raw)
        assert len(result) == 1
        t = result[0]
        assert t["spotify_id"] == "a1"
        assert t["name"] == "Karol G"
        assert t["popularity"] == 90
        assert t["followers_count"] == 5_000_000
        assert t["genres"] == ["reggaeton", "latin pop"]
        assert t["image_url"] == "https://img.com/kg.jpg"

    def test_sin_imagenes_retorna_image_url_none(self):
        raw = [self._artista_raw(image_url=None)]
        result = EtlService.transform_artists(raw)
        assert result[0]["image_url"] is None

    def test_genres_vacio_retorna_lista_vacia(self):
        raw = [self._artista_raw(genres=[])]
        result = EtlService.transform_artists(raw)
        assert result[0]["genres"] == []

    def test_lista_vacia_retorna_vacia(self):
        assert EtlService.transform_artists([]) == []

    def test_multiples_artistas_preservan_orden(self):
        raw = [self._artista_raw(artist_id=f"id{i}", name=f"Artista {i}") for i in range(5)]
        result = EtlService.transform_artists(raw)
        assert len(result) == 5
        for i, item in enumerate(result):
            assert item["spotify_id"] == f"id{i}"


# ─── Endpoint ─────────────────────────────────────────────────────────────────

class TestTopArtistsEndpoint:
    """Tests de integración para GET /v1/artists/top."""

    def test_sin_autenticacion_retorna_403(self, test_client):
        response = test_client.get("/v1/artists/top")
        assert response.status_code == 403

    def test_token_invalido_retorna_401(self, test_client):
        response = test_client.get(
            "/v1/artists/top",
            headers={"Authorization": "Bearer token_invalido"},
        )
        assert response.status_code == 401

    def test_con_token_valido_retorna_200(self, test_client, valid_token):
        response = test_client.get(
            "/v1/artists/top",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    def test_respuesta_tiene_shape_correcto(self, test_client, valid_token):
        response = test_client.get(
            "/v1/artists/top",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert "artists" in data
        assert "total" in data
        assert isinstance(data["artists"], list)
        assert isinstance(data["total"], int)

    def test_sin_datos_retorna_lista_vacia(self, test_client, valid_token):
        response = test_client.get(
            "/v1/artists/top",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        data = response.json()
        assert data["total"] == 0
        assert data["artists"] == []
