"""Pruebas de los géneros revisados a mano."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.v1.services.genre_overrides import apply_genre_overrides, load_overrides


def test_el_archivo_es_valido():
    overrides = load_overrides()
    assert overrides
    for genres in overrides.values():
        assert 1 <= len(genres) <= 3
        assert all(g and g == g.lower().strip() for g in genres)


def test_restaura_solo_los_artistas_distintos():
    (first, first_genres), (second, second_genres) = list(load_overrides().items())[:2]
    wrong = SimpleNamespace(spotify_id=first, genres=["australian"])
    right = SimpleNamespace(spotify_id=second, genres=list(second_genres))
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [wrong, right]

    assert apply_genre_overrides(db) == 1
    assert wrong.genres == first_genres
