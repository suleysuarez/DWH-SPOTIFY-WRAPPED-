"""
filename: config.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Configuración centralizada del backend usando pydantic-settings. Lee y valida
             variables de entorno desde backend/.env. Singleton `settings` compartido por
             todos los módulos.
"""
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configuración de la aplicación leída desde variables de entorno.

    Todos los campos son obligatorios salvo los que tienen valor por defecto.
    Ver `backend/.env` para los valores de desarrollo local.
    """
    # Base de datos
    DATABASE_URL: str = "postgresql://user:password@localhost/dwh"

    # Spotify OAuth
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/v1/auth/callback"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 8

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOW_HOSTS: str = "http://localhost:3000,http://127.0.0.1:3000"

    def get_allow_hosts(self) -> List[str]:
        return [h.strip() for h in self.ALLOW_HOSTS.split(",")]

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()