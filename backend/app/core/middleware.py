"""
filename: middleware.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Middlewares personalizados para FastAPI.
             - RequestLoggingMiddleware: loguea cada request con método, path,
               status code y duración en ms.
             - RateLimitMiddleware: limita requests por IP usando ventana deslizante
               en memoria (suitable para desarrollo; usar Redis en producción).
"""

import os
import time
import logging
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Loguea cada request entrante con: método, path, status code y duración.

    Ejemplo de log:
        INFO: GET /v1/artists/top → 200 (45ms)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)

        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)"
        )
        # Agregar header con duración para debugging en frontend
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiter por IP usando ventana deslizante en memoria.

    Por defecto: máximo 100 requests por minuto por IP.
    Las rutas de health check y docs están exentas.

    Args:
        max_requests (int): Máximo de requests permitidos en la ventana.
        window_seconds (int): Duración de la ventana en segundos.
    """

    EXEMPT_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}
    _instances: list["RateLimitMiddleware"] = []

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # {ip: [timestamp, timestamp, ...]}
        self._requests: dict = defaultdict(list)
        RateLimitMiddleware._instances.append(self)

    @classmethod
    def reset_counters(cls) -> None:
        """Limpia contadores en memoria (aislamiento entre tests de pytest)."""
        for instance in cls._instances:
            instance._requests.clear()

    @staticmethod
    def _is_disabled() -> bool:
        return os.getenv("DISABLE_RATE_LIMIT", "").lower() in ("1", "true", "yes")

    def _get_ip(self, request: Request) -> str:
        """Extrae la IP real considerando proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.EXEMPT_PATHS or self._is_disabled():
            return await call_next(request)

        ip = self._get_ip(request)
        now = time.time()
        window_start = now - self.window_seconds

        # Limpiar timestamps fuera de la ventana
        self._requests[ip] = [t for t in self._requests[ip] if t > window_start]

        if len(self._requests[ip]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self._requests[ip][0]))
            logger.warning(f"[RateLimit] IP {ip} bloqueada — {len(self._requests[ip])} requests en {self.window_seconds}s")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        self._requests[ip].append(now)
        return await call_next(request)
