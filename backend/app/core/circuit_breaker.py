"""
filename: circuit_breaker.py
author: Suley Suárez y Jhonatan Vera
date: 2026-05-15
version: 1.0
description: Implementación del patrón Circuit Breaker para servicios externos
             (Last.fm, Spotify). Protege el sistema de fallos en cascada cuando
             un servicio externo no responde o devuelve errores repetidos.

Estados:
    CLOSED   → funcionando normal, las llamadas pasan.
    OPEN     → demasiados fallos, las llamadas se bloquean por `recovery_timeout` segundos.
    HALF_OPEN → después del timeout, se permite una llamada de prueba.
"""

import time
import logging
import functools
from enum import Enum
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Se lanza cuando el circuito está abierto y se intenta hacer una llamada."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker genérico para proteger llamadas a servicios externos.

    Args:
        name (str): Nombre del servicio (para logs).
        failure_threshold (int): Número de fallos consecutivos antes de abrir el circuito.
        recovery_timeout (int): Segundos que el circuito permanece abierto antes de pasar a HALF_OPEN.
        expected_exception (type): Tipo de excepción que cuenta como fallo.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                logger.info(f"[CircuitBreaker:{self.name}] OPEN → HALF_OPEN (recovery timeout alcanzado)")
                self._state = CircuitState.HALF_OPEN
        return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta la función protegida por el circuit breaker.

        Raises:
            CircuitBreakerError: Si el circuito está OPEN.
        """
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"[CircuitBreaker:{self.name}] Circuito ABIERTO — servicio no disponible temporalmente."
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        if self._state == CircuitState.HALF_OPEN:
            logger.info(f"[CircuitBreaker:{self.name}] HALF_OPEN → CLOSED (llamada exitosa)")
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None

    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        logger.warning(f"[CircuitBreaker:{self.name}] Fallo #{self._failure_count}/{self.failure_threshold}")

        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.error(
                f"[CircuitBreaker:{self.name}] CLOSED → OPEN "
                f"(umbral alcanzado, recovery en {self.recovery_timeout}s)"
            )

    def get_status(self) -> dict:
        """Retorna el estado actual del circuit breaker para monitoreo."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self._last_failure_time,
        }


# Instancias globales — una por servicio externo
lastfm_breaker = CircuitBreaker(
    name="lastfm",
    failure_threshold=5,
    recovery_timeout=60,
)

spotify_breaker = CircuitBreaker(
    name="spotify",
    failure_threshold=3,
    recovery_timeout=30,
)
