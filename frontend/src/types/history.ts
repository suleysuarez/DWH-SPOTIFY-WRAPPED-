/**
 * history.ts — Tipos TypeScript para analíticas del historial de escucha.
 *
 * `PeakHour`       → GET /v1/history/peak-hour
 * `GenreData`      → ítem individual de GET /v1/history/genres
 * `GenresResponse` → respuesta completa de GET /v1/history/genres
 * `QuickStats`     → GET /v1/history/stats (usado en Dashboard para decidir si mostrar EmptyState)
 */

export interface PeakHour {
  hour: number;
  play_count: number;
  label: string; // e.g. "14:00 - 15:00"
}

export interface GenreData {
  genre: string;
  count: number;
  percentage: number;
}

export interface GenresResponse {
  genres: GenreData[];
  total_plays: number;
}

export interface QuickStats {
  total_tracks: number;
  total_artists: number;
  total_plays: number;
  total_minutes: number;
  last_sync: string | null;
  etl_status: "idle" | "running" | "success" | "error";
  top_track: string | null;
  top_track_artist: string | null;
  top_track_plays: number;
}
