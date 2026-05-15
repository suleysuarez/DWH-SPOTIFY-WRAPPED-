/**
 * TopArtistsCard.tsx — Lista de top 5 artistas con imagen y barra de popularidad.
 *
 * Props:
 *   artists → Artist[] | null  (de GET /v1/artists/top, top 5 del array)
 *   loading → boolean
 *   error   → string | null
 *   onRetry → () => void
 *
 * Estados: SkeletonList (cargando) | ErrorState | EmptyState | lista de artistas.
 * Muestra imagen del artista desde `artist.images[0].url`; si no hay imagen,
 * muestra la inicial del nombre con fondo verde Spotify.
 * La barra de popularidad usa `artist.popularity` (0-100).
 */

import type { Artist } from "@/types/artist";
import { SkeletonList } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import { TrendingUp } from "lucide-react";

interface TopArtistsCardProps {
  artists: Artist[] | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export default function TopArtistsCard({
  artists,
  loading,
  error,
  onRetry,
}: TopArtistsCardProps) {
  return (
    <div
      className="glass-card rounded-xl p-5 h-full"
      style={{ minHeight: 320 }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "rgba(29, 185, 84, 0.15)" }}
        >
          <TrendingUp className="w-4 h-4" style={{ color: "#1DB954" }} />
        </div>
        <div>
          <h3
            className="text-sm font-bold text-white"
            style={{ fontFamily: "DM Sans, sans-serif" }}
          >
            Top Artistas
          </h3>
          <p className="text-xs text-white/40">Más escuchados</p>
        </div>
      </div>

      {/* Content */}
      {loading && <SkeletonList rows={5} />}
      {!loading && error && <ErrorState message={error} onRetry={onRetry} />}
      {!loading && !error && (!artists || artists.length === 0) && (
        <EmptyState showEtlLink={false} description="Sincroniza tus datos para ver tus artistas." />
      )}
      {!loading && !error && artists && artists.length > 0 && (
        <ul className="space-y-3">
          {artists.slice(0, 5).map((artist, idx) => (
            <li key={artist.id} className="flex items-center gap-3 group">
              {/* Rank */}
              <span
                className="text-xs font-bold w-5 text-right flex-shrink-0"
                style={{ color: idx === 0 ? "#1DB954" : "rgba(255,255,255,0.3)" }}
              >
                {idx + 1}
              </span>

              {/* Avatar */}
              <div className="w-10 h-10 rounded-full overflow-hidden flex-shrink-0 bg-white/5">
                {artist.images?.[0]?.url ? (
                  <img
                    src={artist.images[0].url}
                    alt={artist.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div
                    className="w-full h-full flex items-center justify-center text-xs font-bold"
                    style={{ background: "rgba(29,185,84,0.2)", color: "#1DB954" }}
                  >
                    {artist.name.charAt(0)}
                  </div>
                )}
              </div>

              {/* Name + popularity */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white truncate">{artist.name}</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-1 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }}>
                    <div
                      className="h-full rounded-full progress-spotify"
                      style={{ width: `${artist.popularity}%` }}
                    />
                  </div>
                  <span className="text-xs text-white/40 flex-shrink-0">{artist.popularity}</span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
