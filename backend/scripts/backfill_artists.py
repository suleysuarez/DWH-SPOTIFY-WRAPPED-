"""
Script de backfill directo para artistas con datos nulos.
Corre sin servidor HTTP ni JWT — conecta a la BD directamente.

Fase 1: Intenta rellenar image_url via Spotify (ID individual → search por nombre).
Fase 2: Rellena popularity y followers_count usando Last.fm listeners (ya implementado
        en EtlService.backfill_artist_stats). Spotify Development Mode no devuelve estos
        campos numéricos, así que Last.fm es la fuente de verdad.

Uso:
    cd backend
    python scripts/backfill_artists.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from app.core.config import settings
from app.models.models import DimUsers, DimArtists
from app.v1.services.spotify_client import SpotifyClient
from app.v1.services.etl_service import EtlService


def main():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()

    try:
        stubs = db.query(DimArtists).filter(
            or_(
                DimArtists.image_url.is_(None),
                DimArtists.popularity.is_(None),
                DimArtists.followers_count.is_(None),
            )
        ).all()

        if not stubs:
            print("No hay artistas con datos faltantes.")
            return

        print(f"Artistas con datos faltantes: {len(stubs)}")

        # ── Fase 1: imágenes via Spotify ─────────────────────────────────────
        needs_image = [a for a in stubs if a.image_url is None]
        if needs_image:
            print(f"\nFase 1: rellenando imágenes para {len(needs_image)} artistas...")

            user = db.query(DimUsers).filter(DimUsers.spotify_refresh_token.isnot(None)).first()
            access_token = None
            if user:
                try:
                    new_tokens = SpotifyClient.refresh_access_token(
                        user.spotify_refresh_token,
                        settings.SPOTIFY_CLIENT_ID,
                        settings.SPOTIFY_CLIENT_SECRET,
                    )
                    access_token = new_tokens["access_token"]
                    user.spotify_access_token = access_token
                    db.commit()
                    print("  Token renovado.")
                except Exception as e:
                    access_token = user.spotify_access_token
                    print(f"  Refresh falló ({e}), usando token existente.")

            search_token = access_token
            if settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
                try:
                    search_token = SpotifyClient.get_client_credentials_token(
                        settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET,
                    )
                    print("  Usando Client Credentials token.")
                except Exception as e:
                    print(f"  CC token falló ({e}), usando user token.")

            if search_token:
                def _fetch(artist):
                    try:
                        result = SpotifyClient.get_artist(search_token, artist.spotify_id)
                        if result:
                            return artist.spotify_id, result
                    except Exception:
                        pass
                    try:
                        result = SpotifyClient.search_artist(search_token, artist.name)
                        return artist.spotify_id, result
                    except Exception:
                        return artist.spotify_id, None

                spotify_map = {}
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futs = {executor.submit(_fetch, a): a for a in needs_image}
                    for fut in as_completed(futs):
                        sid, result = fut.result()
                        if result:
                            spotify_map[sid] = result

                img_updated = 0
                for artist in needs_image:
                    sp = spotify_map.get(artist.spotify_id)
                    if sp:
                        images = sp.get("images") or []
                        if images:
                            artist.image_url = images[0]["url"]
                            img_updated += 1
                db.commit()
                print(f"  Imágenes actualizadas: {img_updated}/{len(needs_image)}")
            else:
                print("  Sin token disponible, saltando fase 1.")

        # ── Fase 2: popularity y followers via Last.fm ────────────────────────
        needs_stats = db.query(DimArtists).filter(
            or_(
                DimArtists.popularity.is_(None),
                DimArtists.followers_count.is_(None),
            )
        ).all()

        if needs_stats:
            print(f"\nFase 2: rellenando popularity/followers via Last.fm para {len(needs_stats)} artistas...")
            if not settings.LASTFM_API_KEY:
                print("  LASTFM_API_KEY no configurado — skipping.")
            else:
                updated = EtlService.backfill_artist_stats(db)
                print(f"  Actualizados: {updated}/{len(needs_stats)}")
        else:
            print("\nFase 2: todos los artistas ya tienen popularity y followers_count.")

        # ── Resumen final ─────────────────────────────────────────────────────
        remaining = db.query(DimArtists).filter(
            or_(
                DimArtists.image_url.is_(None),
                DimArtists.popularity.is_(None),
                DimArtists.followers_count.is_(None),
            )
        ).count()
        print(f"\nArtistas aún con datos faltantes: {remaining}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
