"""
filename: sync_etl.py
description: Sincronización automática. Ejecuta el mismo pipeline de POST /v1/etl/run para
             cada usuario con refresh token, sin necesidad de tener el servidor encendido.
             El detalle va a backend/logs/sync.log. Por consola solo sale un resumen sin datos
             de usuarios, porque los registros de GitHub Actions de un repo público son visibles.
             La programa .github/workflows/sync-etl.yml.

Uso (desde cualquier carpeta):
    python backend/scripts/sync_etl.py
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
os.chdir(BACKEND_DIR)  # la configuración lee .env desde la carpeta actual
sys.path.insert(0, str(BACKEND_DIR))

LOG_DIR = BACKEND_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# El detalle (que puede incluir identificadores y URLs) solo va a archivo.
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(LOG_DIR / "sync.log", maxBytes=500_000, backupCount=2, encoding="utf-8")],
)
logger = logging.getLogger("sync_etl")
logger.setLevel(logging.INFO)


def report(message: str) -> None:
    """Resumen público: nunca incluir identificadores, tokens ni mensajes de error."""
    print(message, flush=True)


def main() -> int:
    from app.core.database import get_db
    from app.models.models import DimUsers
    from app.v1.routers.etl import run_etl

    db_gen = get_db()
    db = next(db_gen)
    failures = 0
    try:
        users = db.query(DimUsers).filter(DimUsers.spotify_refresh_token.isnot(None)).all()
        if not users:
            logger.info("No hay usuarios para sincronizar. Inicia sesión en la aplicación al menos una vez.")
            report("No hay usuarios para sincronizar.")
            return 0

        for user in users:
            spotify_id, number = user.spotify_id, user.user_id
            try:
                result = run_etl(current_user=user, db=db)
                if result["status"] != "success":
                    failures += 1
                    logger.error("ETL de %s falló: %s", spotify_id, result["message"])
                    report(f"usuario {number}: error")
                    continue
                logger.info("ETL de %s correcto: %s reproducciones nuevas",
                            spotify_id, result["summary"]["history_new"])
                report(f"usuario {number}: {result['summary']['history_new']} reproducciones nuevas")
            except Exception as exc:  # un usuario con error no debe frenar a los demás
                db.rollback()
                failures += 1
                logger.error("ETL de %s falló: %s", spotify_id, getattr(exc, "detail", exc))
                report(f"usuario {number}: error ({type(exc).__name__})")
    finally:
        db_gen.close()

    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        logger.exception("La sincronización no pudo ejecutarse")
        report(f"La sincronización no pudo ejecutarse ({type(exc).__name__})")
        sys.exit(1)
