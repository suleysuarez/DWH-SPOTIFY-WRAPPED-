/**
 * artist.ts — Tipos TypeScript para artistas del DWH.
 *
 * `Artist` mapea la respuesta de GET /v1/artists/top (schema ArtistResponse del backend).
 * `images` se recibe pero no se usa en TopArtistsCard (que muestra un emoji placeholder).
 * `play_count` y `rank` son campos opcionales calculados desde fact_listening_history.
 */

export interface Artist {
  id: string;
  name: string;
  popularity: number;
  genres: string[];
  images: Array<{ url: string; width: number; height: number }>;
  external_urls: { spotify: string };
  play_count?: number;
  rank?: number;
}

export interface TopArtistsResponse {
  artists: Artist[];
  total: number;
}
