"""
filename: test_profile.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Tests de integración para GET /v1/profile/me. Verifica autenticación,
             shape del response y corrección de los campos serializados desde DimUsers.
"""


def test_perfil_sin_autenticacion_retorna_403(test_client):
    response = test_client.get("/v1/profile/me")
    assert response.status_code == 403


def test_perfil_con_token_invalido_retorna_401(test_client):
    response = test_client.get(
        "/v1/profile/me",
        headers={"Authorization": "Bearer token.invalido.aqui"},
    )
    assert response.status_code == 401


def test_perfil_con_token_valido_retorna_200(test_client, valid_token):
    response = test_client.get(
        "/v1/profile/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200


def test_perfil_shape_contiene_campos_requeridos(test_client, valid_token):
    response = test_client.get(
        "/v1/profile/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    data = response.json()
    campos = {"spotify_id", "display_name", "email", "country", "followers", "product", "user_id"}
    for campo in campos:
        assert campo in data, f"Campo '{campo}' ausente en la respuesta"


def test_perfil_retorna_datos_del_usuario_simulado(test_client, valid_token, fake_user):
    response = test_client.get(
        "/v1/profile/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    data = response.json()
    assert data["spotify_id"] == fake_user.spotify_id
    assert data["display_name"] == fake_user.display_name
    assert data["email"] == fake_user.email
    assert data["country"] == fake_user.country
    assert data["user_id"] == fake_user.user_id
    assert data["product"] == fake_user.product


def test_perfil_image_url_presente(test_client, valid_token, fake_user):
    response = test_client.get(
        "/v1/profile/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    data = response.json()
    assert "image_url" in data
    assert data["image_url"] == fake_user.image_url
