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
