/**
 * user.ts — Tipos TypeScript para el perfil de usuario.
 *
 * `SpotifyUser` refleja el subset de campos de Spotify almacenados en dim_users del DWH.
 * `UserProfile` extiende SpotifyUser con `last_sync` (timestamp del último ETL exitoso).
 * La fuente de datos es GET /v1/profile/me (DWH, no la API de Spotify en tiempo real).
 */

export interface SpotifyUser {
  spotify_id: string;
  display_name: string;
  email: string;
  country: string;
  followers: number;
  product: "free" | "premium" | "open";
  image_url?: string;
}

export interface UserProfile extends SpotifyUser {
  user_id: number;
  loaded_at: string;
}
