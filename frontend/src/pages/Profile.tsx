/**
 * Profile Page
 * API: GET /v1/profile/me
 * Design: Glassmorphism Premium Dark — hero card + stat cards
 */

import AppLayout from "@/components/layout/AppLayout";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import type { UserProfile } from "@/types/user";
import { SkeletonCard } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import { ExternalLink, MapPin, Mail, Users, Star, Crown } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Profile() {
  const { data: user, loading, error, refetch } = useApi<UserProfile>(endpoints.profile.me);

  return (
    <AppLayout>
      <div className="mb-8">
        <h1
          className="text-3xl font-black text-white mb-1"
          style={{ fontFamily: "Nunito, sans-serif" }}
        >
          Perfil
        </h1>
        <p className="text-sm text-white/40">Tu cuenta de Spotify conectada.</p>
      </div>

      {loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <SkeletonCard className="lg:col-span-1" />
          <div className="lg:col-span-2 grid grid-cols-2 gap-4">
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Hero card */}
          <div
            className="glass-card rounded-xl p-8 flex flex-col items-center text-center lg:col-span-1"
            style={{
              background: "linear-gradient(160deg, rgba(29,185,84,0.08) 0%, rgba(24,24,24,0.9) 60%)",
              border: "1px solid rgba(29,185,84,0.12)",
            }}
          >
            {/* Avatar */}
            <div className="relative mb-5">
              <div
                className="w-24 h-24 rounded-full overflow-hidden"
                style={{
                  border: "3px solid #1DB954",
                  boxShadow: "0 0 24px rgba(29,185,84,0.35)",
                }}
              >
                {user.images?.[0]?.url ? (
                  <img
                    src={user.images[0].url}
                    alt={user.display_name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div
                    className="w-full h-full flex items-center justify-center text-3xl font-black"
                    style={{ background: "rgba(29,185,84,0.2)", color: "#1DB954" }}
                  >
                    {user.display_name?.charAt(0) ?? "?"}
                  </div>
                )}
              </div>

              {/* Premium badge */}
              {user.product === "premium" && (
                <div
                  className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full flex items-center justify-center"
                  style={{ background: "#FFD700", boxShadow: "0 2px 8px rgba(255,215,0,0.4)" }}
                  title="Premium"
                >
                  <Crown className="w-3.5 h-3.5 text-black" />
                </div>
              )}
            </div>

            {/* Name */}
            <h2
              className="text-xl font-black text-white mb-1"
              style={{ fontFamily: "Nunito, sans-serif" }}
            >
              {user.display_name}
            </h2>

            {/* Product badge */}
            <span
              className="text-xs font-bold px-3 py-1 rounded-full mb-4"
              style={
                user.product === "premium"
                  ? { background: "rgba(255,215,0,0.15)", color: "#FFD700", border: "1px solid rgba(255,215,0,0.3)" }
                  : { background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.1)" }
              }
            >
              {user.product === "premium" ? "✦ Premium" : "Free"}
            </span>

            {/* External link */}
            {user.external_urls?.spotify && (
              <a
                href={user.external_urls.spotify}
                target="_blank"
                rel="noopener noreferrer"
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

          {/* Stats grid */}
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Email */}
            <div className="glass-card rounded-xl p-5">
              <div className="flex items-center gap-3 mb-2">
                <Mail className="w-4 h-4 text-white/30" />
                <span className="text-xs text-white/40">Email</span>
              </div>
              <p className="text-sm font-semibold text-white truncate">{user.email || "—"}</p>
            </div>

            {/* Country */}
            <div className="glass-card rounded-xl p-5">
              <div className="flex items-center gap-3 mb-2">
                <MapPin className="w-4 h-4 text-white/30" />
                <span className="text-xs text-white/40">País</span>
              </div>
              <p className="text-sm font-semibold text-white">{user.country || "—"}</p>
            </div>

            {/* Followers */}
            <div className="glass-card rounded-xl p-5">
              <div className="flex items-center gap-3 mb-2">
                <Users className="w-4 h-4 text-white/30" />
                <span className="text-xs text-white/40">Seguidores</span>
              </div>
              <p
                className="text-2xl font-black"
                style={{ fontFamily: "Nunito, sans-serif", color: "#1DB954" }}
              >
                {user.followers?.toLocaleString() ?? "—"}
              </p>
            </div>

            {/* Plan */}
            <div className="glass-card rounded-xl p-5">
              <div className="flex items-center gap-3 mb-2">
                <Star className="w-4 h-4 text-white/30" />
                <span className="text-xs text-white/40">Plan</span>
              </div>
              <p
                className="text-sm font-bold capitalize"
                style={{ color: user.product === "premium" ? "#FFD700" : "rgba(255,255,255,0.6)" }}
              >
                {user.product === "premium" ? "✦ Premium" : "Free"}
              </p>
            </div>

            {/* Spotify ID */}
            <div className="glass-card rounded-xl p-5 sm:col-span-2">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs text-white/40">Spotify ID</span>
              </div>
              <p className="text-xs font-mono text-white/50 break-all">{user.id}</p>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
