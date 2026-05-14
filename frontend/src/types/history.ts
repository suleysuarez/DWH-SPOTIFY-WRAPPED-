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
  last_sync: string | null;
  etl_status: "idle" | "running" | "success" | "error";
}
