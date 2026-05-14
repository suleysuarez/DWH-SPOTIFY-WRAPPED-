export interface SpotifyUser {
  id: string;
  display_name: string;
  email: string;
  country: string;
  followers: number;
  product: "free" | "premium" | "open";
  images: Array<{ url: string; width: number; height: number }>;
  external_urls: { spotify: string };
}

export interface UserProfile extends SpotifyUser {
  last_sync?: string;
}
