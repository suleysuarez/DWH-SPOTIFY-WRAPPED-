"""
repair_dwh.py — Repara datos corruptos en el DWH.

Problemas que corrige:
  1. dim_artists.popularity > 100 (eran listener counts de Last.fm guardados por error)
     → reset a NULL y recalcula desde Spotify GET /v1/artists
  2. dim_tracks.popularity NULL (la API recently-played no devuelve ese campo)
     → rellena desde Spotify GET /v1/tracks
  3. dim_artists.genres con sentinel [''] (Last.fm no encontró el artista en ese momento)
     → reintenta con Last.fm ahora

Uso:
    cd backend
    python repair_dwh.py
"""

import os
import sys
import math
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

if not DATABASE_URL:
    sys.exit("DATABASE_URL no encontrada en .env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

pg_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
engine = create_engine(pg_url)
Session = sessionmaker(bind=engine)

# ── Helpers Spotify ────────────────────────────────────────────────────────────

def get_cc_token() -> str:
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def spotify_get_artists(token: str, ids: list) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    for i in range(0, len(ids), 50):
        batch = ids[i:i+50]
        r = requests.get(
            "https://api.spotify.com/v1/artists",
            headers=headers,
            params={"ids": ",".join(batch)},
            timeout=15,
        )
        r.raise_for_status()
        results.extend(r.json().get("artists") or [])
        if i + 50 < len(ids):
            time.sleep(0.1)
    return results


def spotify_get_tracks(token: str, ids: list) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    for i in range(0, len(ids), 50):
        batch = ids[i:i+50]
        r = requests.get(
            "https://api.spotify.com/v1/tracks",
            headers=headers,
            params={"ids": ",".join(batch)},
            timeout=15,
        )
        r.raise_for_status()
        results.extend(r.json().get("tracks") or [])
        if i + 50 < len(ids):
            time.sleep(0.1)
    return results


# ── Helper Last.fm ─────────────────────────────────────────────────────────────

def lastfm_genres(name: str) -> list:
    if not LASTFM_API_KEY:
        return []
    try:
        r = requests.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={"method": "artist.getTopTags", "artist": name,
                    "api_key": LASTFM_API_KEY, "format": "json", "autocorrect": 1},
            timeout=4,
        )
        tags = r.json().get("toptags", {}).get("tag", [])
        return [t["name"].lower() for t in tags[:5] if t.get("name")]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Reparar dim_artists.popularity (reset + Spotify)
# ══════════════════════════════════════════════════════════════════════════════

def fix_artist_popularity():
    print("\n=== PASO 1: Reparar popularity de artistas ===")
    db = Session()
    try:
        # Reset valores corruptos (> 100 no es popularity de Spotify)
        result = db.execute(text(
            "UPDATE dwh.dim_artists SET popularity = NULL WHERE popularity > 100"
        ))
        corrupted = result.rowcount
        db.commit()
        print(f"  Reseteados {corrupted} artistas con popularity > 100")

        # Obtener todos los spotify_id para recalcular
        rows = db.execute(text("SELECT artist_id, spotify_id FROM dwh.dim_artists")).fetchall()
        all_ids = [r[1] for r in rows]
        id_map  = {r[1]: r[0] for r in rows}  # spotify_id → artist_id

        print(f"  Obteniendo popularity real para {len(all_ids)} artistas desde Spotify...")
        token = get_cc_token()
        items = spotify_get_artists(token, all_ids)

        updated = 0
        for item in items:
            if not item:
                continue
            pop = item.get("popularity")
            if pop is None:
                continue
            db.execute(text(
                "UPDATE dwh.dim_artists SET popularity = :pop WHERE spotify_id = :sid"
            ), {"pop": pop, "sid": item["id"]})
            updated += 1

        db.commit()
        print(f"  Actualizada popularity (0-100) en {updated}/{len(all_ids)} artistas")

        # Verificar
        r = db.execute(text(
            "SELECT MIN(popularity), MAX(popularity), AVG(popularity)::int, "
            "SUM(CASE WHEN popularity IS NULL THEN 1 ELSE 0 END) "
            "FROM dwh.dim_artists"
        )).fetchone()
        print(f"  Resultado: min={r[0]}, max={r[1]}, avg={r[2]}, nulls={r[3]}")
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Rellenar dim_tracks.popularity
# ══════════════════════════════════════════════════════════════════════════════

def fix_track_popularity():
    print("\n=== PASO 2: Rellenar popularity de tracks ===")
    db = Session()
    try:
        rows = db.execute(text(
            "SELECT track_id, spotify_id FROM dwh.dim_tracks WHERE popularity IS NULL"
        )).fetchall()
        if not rows:
            print("  Ningún track con popularity NULL. Nada que hacer.")
            return

        print(f"  {len(rows)} tracks con popularity NULL — llamando Spotify...")
        track_ids = [r[1] for r in rows]

        token = get_cc_token()
        items = spotify_get_tracks(token, track_ids)

        updated = 0
        for item in items:
            if not item:
                continue
            pop = item.get("popularity")
            if pop is None:
                continue
            db.execute(text(
                "UPDATE dwh.dim_tracks SET popularity = :pop WHERE spotify_id = :sid"
            ), {"pop": pop, "sid": item["id"]})
            updated += 1

        db.commit()
        print(f"  Actualizada popularity en {updated}/{len(rows)} tracks")

        r = db.execute(text(
            "SELECT SUM(CASE WHEN popularity IS NULL THEN 1 ELSE 0 END), COUNT(*) FROM dwh.dim_tracks"
        )).fetchone()
        print(f"  Resultado: {r[0]} nulls restantes de {r[1]} tracks")
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — Re-intentar géneros con Last.fm (solo artistas con sentinel [''])
# ══════════════════════════════════════════════════════════════════════════════

def fix_artist_genres():
    print("\n=== PASO 3: Rellenar géneros de artistas (Last.fm) ===")
    if not LASTFM_API_KEY:
        print("  LASTFM_API_KEY no configurada — omitiendo")
        return

    db = Session()
    try:
        rows = db.execute(text(
            "SELECT artist_id, name FROM dwh.dim_artists "
            "WHERE genres = ARRAY['']::varchar[] OR cardinality(genres) = 0"
        )).fetchall()
        if not rows:
            print("  No hay artistas sin géneros. Nada que hacer.")
            return

        print(f"  {len(rows)} artistas sin géneros — consultando Last.fm en paralelo...")

        # Llamadas paralelas (max 10)
        results: dict = {}
        with ThreadPoolExecutor(max_workers=10) as ex:
            fut_map = {ex.submit(lastfm_genres, r[1]): r for r in rows}
            for fut in as_completed(fut_map):
                row = fut_map[fut]
                try:
                    results[row[0]] = fut.result()
                except Exception:
                    results[row[0]] = []

        updated = 0
        for row in rows:
            artist_id, name = row
            genres = results.get(artist_id, [])
            new_genres = genres if genres else [""]
            db.execute(text(
                "UPDATE dwh.dim_artists SET genres = :g WHERE artist_id = :id"
            ), {"g": new_genres, "id": artist_id})
            if genres:
                updated += 1

        db.commit()
        print(f"  Géneros encontrados para {updated}/{len(rows)} artistas")

        r = db.execute(text(
            "SELECT SUM(CASE WHEN genres = ARRAY['']::varchar[] THEN 1 ELSE 0 END) "
            "FROM dwh.dim_artists"
        )).fetchone()
        print(f"  Artistas que siguen sin géneros en Last.fm: {r[0]} (artistas muy locales/nuevos)")
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t0 = time.time()
    print("Iniciando reparación del DWH...")

    fix_artist_popularity()
    fix_track_popularity()
    fix_artist_genres()

    print(f"\nReparación completada en {time.time()-t0:.1f}s")
