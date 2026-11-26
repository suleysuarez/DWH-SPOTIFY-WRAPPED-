"""
Géneros revisados a mano (app/data/genre_overrides.json, por spotify_id de artista).

Las etiquetas de Last.fm suelen ser erróneas (países, "american idol", "psytrance" para un grupo
de adoración) y el ETL las vuelve a escribir. Este paso, al final de cada ejecución, restaura las revisadas.
Para corregir otro artista basta con añadirlo al JSON.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.models import DimArtists

OVERRIDES_PATH = Path(__file__).resolve().parents[2] / "data" / "genre_overrides.json"


@lru_cache(maxsize=1)
def load_overrides() -> Dict[str, List[str]]:
    with OVERRIDES_PATH.open(encoding="utf-8") as file:
        return {spotify_id: item["genres"] for spotify_id, item in json.load(file).items()}


def apply_genre_overrides(db: Session) -> int:
    """Restaura los géneros revisados. Retorna cuántos artistas cambiaron (sin commit)."""
    overrides = load_overrides()
    changed = 0
    for artist in db.query(DimArtists).filter(DimArtists.spotify_id.in_(list(overrides))).all():
        genres = overrides.get(artist.spotify_id)
        if genres and artist.genres != genres:
            artist.genres = list(genres)
            changed += 1
    return changed
