/**
 * track.ts — Tipos TypeScript para canciones del DWH.
 *
 * `Track` mapea la respuesta de GET /v1/tracks/top (schema TrackResponse del backend).
 * `album_image` corresponde al campo `album_image_url` de dim_tracks en el DWH.
 * `formatDuration(ms)` convierte milisegundos a "mm:ss" — usado en TopTracksCard.tsx.
 */

export interface Track {
  id: string;
  name: string;
  artist_name: string;
  album_name: string;
  duration_ms: number;
  popularity: number;
  preview_url?: string;
  external_urls: { spotify: string };
  album_image?: string;
  play_count?: number;
  rank?: number;
}

export interface TopTracksResponse {
  tracks: Track[];
  total: number;
}

/** Format milliseconds to mm:ss */
export function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}
