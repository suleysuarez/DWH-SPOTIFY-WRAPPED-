/**
 * TopTracksCard — displays top tracks with name, artist, and duration.
 */

import type { Track } from "@/types/track";
import { formatDuration } from "@/types/track";
import { SkeletonList } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import { Music } from "lucide-react";

interface TopTracksCardProps {
  tracks: Track[] | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export default function TopTracksCard({
  tracks,
  loading,
  error,
  onRetry,
}: TopTracksCardProps) {
  return (
    <div className="glass-card rounded-xl p-5 h-full" style={{ minHeight: 320 }}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "rgba(29, 185, 84, 0.15)" }}
        >
          <Music className="w-4 h-4" style={{ color: "#1DB954" }} />
        </div>
        <div>
          <h3
            className="text-sm font-bold text-white"
            style={{ fontFamily: "Nunito, sans-serif" }}
          >
            Top Canciones
          </h3>
          <p className="text-xs text-white/40">Más reproducidas</p>
        </div>
      </div>

      {/* Content */}
      {loading && <SkeletonList rows={5} />}
      {!loading && error && <ErrorState message={error} onRetry={onRetry} />}
      {!loading && !error && (!tracks || tracks.length === 0) && (
        <EmptyState showEtlLink={false} description="Sincroniza tus datos para ver tus canciones." />
      )}
      {!loading && !error && tracks && tracks.length > 0 && (
        <ul className="space-y-3">
          {tracks.slice(0, 5).map((track, idx) => (
            <li key={track.id} className="flex items-center gap-3 group">
              {/* Rank */}
              <span
                className="text-xs font-bold w-5 text-right flex-shrink-0"
                style={{ color: idx === 0 ? "#1DB954" : "rgba(255,255,255,0.3)" }}
              >
                {idx + 1}
              </span>

              {/* Album art */}
              <div className="w-10 h-10 rounded-md overflow-hidden flex-shrink-0 bg-white/5">
                {track.album_image ? (
                  <img
                    src={track.album_image}
                    alt={track.album_name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div
                    className="w-full h-full flex items-center justify-center"
                    style={{ background: "rgba(29,185,84,0.1)" }}
                  >
                    <Music className="w-4 h-4" style={{ color: "#1DB954" }} />
                  </div>
                )}
              </div>

              {/* Track info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white truncate">{track.name}</p>
                <p className="text-xs text-white/40 truncate">{track.artist_name}</p>
              </div>

              {/* Duration */}
              <span className="text-xs text-white/30 flex-shrink-0 font-mono">
                {formatDuration(track.duration_ms)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
