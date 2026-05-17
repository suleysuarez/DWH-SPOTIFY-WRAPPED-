/**
 * Profile.tsx — Página de perfil del usuario autenticado.
 *
 * Carga los datos desde GET /v1/profile/me (fuente: dwh.dim_users).
 * La foto de perfil viene de `image_url` (extraída de Spotify en el login/ETL).
 * El enlace de Spotify se construye a partir de `spotify_id`.
 *
 * Autores: Suley Suárez y Jhonatan Vera
 */

import AppLayout from "@/components/layout/AppLayout";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import type { UserProfile } from "@/types/user";
import { SkeletonCard } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import { ExternalLink, MapPin, Mail, Users, Star, Crown, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export default function Profile() {
  const { data: user, loading, error, refetch } = useApi<UserProfile>(endpoints.profile.me);
  const [showSpotifyId, setShowSpotifyId] = useState(false);

  const spotifyUrl = user?.spotify_id
    ? `https://open.spotify.com/user/${user.spotify_id}`
    : null;

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-black text-white mb-1">Perfil</h1>
        <p className="text-sm text-white/40">Tu cuenta de Spotify conectada.</p>
      </div>

      {loading && (
        <div className="space-y-5">
          <SkeletonCard className="h-52" />
          <div className="grid grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="glass-card rounded-xl p-8">
          <ErrorState message={error} onRetry={refetch} />
        </div>
      )}

      {!loading && !error && user && (
        <div className="space-y-5">

          {/* ── HERO ── */}
          <div
            className="relative overflow-hidden rounded-2xl p-8"
            style={{
              background: "linear-gradient(135deg, rgba(29,185,84,0.13) 0%, rgba(22,22,22,0.97) 55%, rgba(29,185,84,0.07) 100%)",
              border: "1px solid rgba(29,185,84,0.18)",
            }}
          >
            {/* Ambient glow blobs */}
            <div
              className="absolute pointer-events-none"
              style={{
                top: "-80px", left: "-80px",
                width: 280, height: 280,
                borderRadius: "50%",
                background: "radial-gradient(circle, rgba(29,185,84,0.18) 0%, transparent 70%)",
                filter: "blur(50px)",
              }}
            />
            <div
              className="absolute pointer-events-none"
              style={{
                bottom: "-60px", right: "-60px",
                width: 200, height: 200,
                borderRadius: "50%",
                background: "radial-gradient(circle, rgba(29,185,84,0.10) 0%, transparent 70%)",
                filter: "blur(40px)",
              }}
            />

            <div className="relative z-10 flex flex-col sm:flex-row items-center sm:items-start gap-7">

              {/* Avatar */}
              <div className="relative flex-shrink-0">
                <div
                  className="w-28 h-28 sm:w-32 sm:h-32 rounded-full overflow-hidden"
                  style={{
                    border: "3px solid #1DB954",
                    boxShadow: "0 0 32px rgba(29,185,84,0.45), 0 0 70px rgba(29,185,84,0.18)",
                  }}
                >
                  {user.image_url ? (
                    <img
                      src={user.image_url}
                      alt={user.display_name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div
                      className="w-full h-full flex items-center justify-center text-4xl font-black"
                      style={{ background: "rgba(29,185,84,0.2)", color: "#1DB954" }}
                    >
                      {user.display_name?.charAt(0)?.toUpperCase() ?? "?"}
                    </div>
                  )}
                </div>

                {user.product === "premium" && (
                  <div
                    className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full flex items-center justify-center"
                    style={{ background: "#FFD700", boxShadow: "0 2px 10px rgba(255,215,0,0.55)" }}
                    title="Cuenta Premium"
                  >
                    <Crown className="w-4 h-4 text-black" />
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="flex flex-col items-center sm:items-start text-center sm:text-left flex-1 min-w-0">
                <h2 className="text-2xl sm:text-3xl font-black text-white mb-3 truncate max-w-full">
                  {user.display_name || "—"}
                </h2>

                <div className="flex flex-wrap justify-center sm:justify-start gap-2 mb-5">
                  <span
                    className="text-xs font-bold px-3 py-1.5 rounded-full"
                    style={
                      user.product === "premium"
                        ? { background: "rgba(255,215,0,0.15)", color: "#FFD700", border: "1px solid rgba(255,215,0,0.3)" }
                        : { background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.1)" }
                    }
                  >
                    {user.product === "premium" ? "✦ Premium" : "Free"}
                  </span>
                  {user.country && (
                    <span
                      className="text-xs font-medium px-3 py-1.5 rounded-full"
                      style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.08)" }}
                    >
                      {user.country}
                    </span>
                  )}
                </div>

                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-black" style={{ color: "#1DB954" }}>
                    {user.followers?.toLocaleString() ?? "0"}
                  </span>
                  <span className="text-sm text-white/40">seguidores en Spotify</span>
                </div>
              </div>

              {/* External link */}
              {spotifyUrl && (
                <a
                  href={spotifyUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="sm:ml-auto flex-shrink-0 self-start"
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2 border-white/10 text-white/60 hover:text-white hover:border-white/20"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Ver en Spotify
                  </Button>
                </a>
              )}
            </div>
          </div>

          {/* ── STATS GRID ── */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

            {/* Email */}
            <div className="glass-card rounded-xl p-5">
              <div className="flex items-center gap-2.5 mb-3">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(29,185,84,0.12)" }}
                >
                  <Mail className="w-3.5 h-3.5" style={{ color: "#1DB954" }} />
                </div>
                <span className="text-xs text-white/40 font-medium">Email</span>
              </div>
              <p className="text-sm font-semibold text-white truncate">{user.email || "—"}</p>
            </div>

            {/* País */}
            <div className="glass-card rounded-xl p-5">
              <div className="flex items-center gap-2.5 mb-3">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(29,185,84,0.12)" }}
                >
                  <MapPin className="w-3.5 h-3.5" style={{ color: "#1DB954" }} />
                </div>
                <span className="text-xs text-white/40 font-medium">País</span>
              </div>
              <p className="text-sm font-semibold text-white">{user.country || "—"}</p>
            </div>

            {/* Seguidores */}
            <div
              className="glass-card rounded-xl p-5"
              style={{ border: "1px solid rgba(29,185,84,0.2)" }}
            >
              <div className="flex items-center gap-2.5 mb-3">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(29,185,84,0.12)" }}
                >
                  <Users className="w-3.5 h-3.5" style={{ color: "#1DB954" }} />
                </div>
                <span className="text-xs text-white/40 font-medium">Seguidores</span>
              </div>
              <p className="text-2xl font-black" style={{ color: "#1DB954" }}>
                {user.followers?.toLocaleString() ?? "—"}
              </p>
            </div>

            {/* Plan */}
            <div className="glass-card rounded-xl p-5">
              <div className="flex items-center gap-2.5 mb-3">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{
                    background: user.product === "premium"
                      ? "rgba(255,215,0,0.12)"
                      : "rgba(29,185,84,0.12)",
                  }}
                >
                  {user.product === "premium"
                    ? <Crown className="w-3.5 h-3.5" style={{ color: "#FFD700" }} />
                    : <Star className="w-3.5 h-3.5" style={{ color: "#1DB954" }} />
                  }
                </div>
                <span className="text-xs text-white/40 font-medium">Plan</span>
              </div>
              <p
                className="text-sm font-bold"
                style={{ color: user.product === "premium" ? "#FFD700" : "rgba(255,255,255,0.6)" }}
              >
                {user.product === "premium" ? "✦ Premium" : "Free"}
              </p>
            </div>

            {/* Spotify ID */}
            <div className="sm:col-span-2 glass-card rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: "rgba(255,255,255,0.06)" }}
                  >
                    <span className="text-xs font-bold text-white/30">ID</span>
                  </div>
                  <span className="text-xs text-white/40 font-medium">Spotify ID</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowSpotifyId((v) => !v)}
                  className="flex items-center gap-1 text-xs text-white/30 hover:text-white/60 transition-colors"
                  title={showSpotifyId ? "Ocultar" : "Mostrar"}
                >
                  {showSpotifyId
                    ? <EyeOff className="w-3.5 h-3.5" />
                    : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
              <p className="text-xs font-mono text-white/50 break-all">
                {showSpotifyId
                  ? (user.spotify_id || "—")
                  : "•".repeat(Math.min(user.spotify_id?.length ?? 8, 24))}
              </p>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
