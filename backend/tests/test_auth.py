"""
filename: test_auth.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Tests unitarios para AuthService: generación de par PKCE, state CSRF y ciclo
             completo de JWT (create / verify / expirado / manipulado).
"""

import jwt
import pytest
from app.v1.services.auth_service import AuthService


class TestPkce:
    """Tests para generación del par code_verifier / code_challenge."""

    def test_genera_verifier_y_challenge_como_strings(self):
        verifier, challenge = AuthService.generate_pkce_pair()
        assert isinstance(verifier, str) and len(verifier) > 0
        assert isinstance(challenge, str) and len(challenge) > 0

    def test_verifier_y_challenge_son_distintos(self):
        verifier, challenge = AuthService.generate_pkce_pair()
        assert verifier != challenge

    def test_pares_pkce_son_unicos_entre_llamadas(self):
        par1 = AuthService.generate_pkce_pair()
        par2 = AuthService.generate_pkce_pair()
        assert par1[0] != par2[0], "El code_verifier debe ser aleatorio en cada llamada"

    def test_challenge_tiene_formato_base64url(self):
        _, challenge = AuthService.generate_pkce_pair()
        import re
        assert re.match(r"^[A-Za-z0-9_\-]+$", challenge), "El challenge debe ser Base64URL sin padding"


class TestState:
    """Tests para generación del state CSRF."""

    def test_genera_state_no_vacio(self):
        state = AuthService.generate_state()
        assert isinstance(state, str) and len(state) > 0

    def test_states_son_unicos(self):
        estados = {AuthService.generate_state() for _ in range(5)}
        assert len(estados) == 5, "Cada state debe ser único"


class TestJwt:
    """Tests para creación y verificación de JWT."""

    def test_crea_token_como_string(self):
        token = AuthService.create_jwt_token("spotify123")
        assert isinstance(token, str) and len(token) > 0

    def test_payload_contiene_sub_correcto(self):
        token = AuthService.create_jwt_token("spotify_abc")
        payload = AuthService.verify_jwt_token(token)
        assert payload["sub"] == "spotify_abc"

    def test_payload_contiene_iat_y_exp(self):
        token = AuthService.create_jwt_token("user1")
        payload = AuthService.verify_jwt_token(token)
        assert "iat" in payload
        assert "exp" in payload

    def test_exp_posterior_a_iat(self):
        token = AuthService.create_jwt_token("user1")
        payload = AuthService.verify_jwt_token(token)
        assert payload["exp"] > payload["iat"]

    def test_token_invalido_lanza_invalid_token_error(self):
        with pytest.raises(jwt.InvalidTokenError):
            AuthService.verify_jwt_token("token.invalido.aqui")

    def test_token_con_firma_manipulada_lanza_excepcion(self):
        token = AuthService.create_jwt_token("user1")
        partes = token.split(".")
        partes[2] = "FIRMA_MANIPULADA_XXXXX"
        manipulado = ".".join(partes)
        with pytest.raises(jwt.InvalidTokenError):
            AuthService.verify_jwt_token(manipulado)

    def test_token_vacio_lanza_excepcion(self):
        with pytest.raises(jwt.InvalidTokenError):
            AuthService.verify_jwt_token("")
