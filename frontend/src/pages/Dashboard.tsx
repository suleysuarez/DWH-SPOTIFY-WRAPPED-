/**
 * Dashboard.tsx — Compone las secciones del resumen. Cada sección vive en
 * components/dashboard/sections/; aquí solo se cargan los datos y se reparten.
 */
import { useRef } from "react";
import AppLayout from "@/components/layout/AppLayout";
import EmptyState from "@/components/ui/EmptyState";
import QuickStatsCards from "@/components/dashboard/QuickStatsCards";
import SpotifyFloatingPlayer from "@/components/dashboard/SpotifyFloatingPlayer";
import HeroSection from "@/components/dashboard/sections/HeroSection";
import TopArtistsSection from "@/components/dashboard/sections/TopArtistsSection";
import TopTracksSection from "@/components/dashboard/sections/TopTracksSection";
import GenresSection from "@/components/dashboard/sections/GenresSection";
import MinutesSection from "@/components/dashboard/sections/MinutesSection";
import FavoriteSongSection from "@/components/dashboard/sections/FavoriteSongSection";
import PeakHourSection from "@/components/dashboard/sections/PeakHourSection";
import ExplorerSection from "@/components/dashboard/sections/ExplorerSection";
import SearchSection from "@/components/dashboard/sections/SearchSection";
import ThanksSection from "@/components/dashboard/sections/ThanksSection";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import type { TopArtistsResponse } from "@/types/artist";
import type { TopTracksResponse } from "@/types/track";
import type { GenresResponse, QuickStats } from "@/types/history";

export default function Dashboard() {
  const artists = useApi<TopArtistsResponse>(endpoints.artists.top);
  const tracks  = useApi<TopTracksResponse>(endpoints.tracks.top);
  const genres  = useApi<GenresResponse>(endpoints.history.genres);
  const stats   = useApi<QuickStats>(endpoints.history.quickStats);
  // El reproductor flotante se alinea sobre este hueco de la sección "canción favorita".
  const placeholderRef = useRef<HTMLDivElement>(null);

  const isDwhEmpty =
    !stats.loading && !stats.error && stats.data &&
    stats.data.total_tracks === 0 && stats.data.total_artists === 0;

  return (
    <AppLayout>
      <SpotifyFloatingPlayer
        topTrack={stats.data?.top_track ?? null}
        topTrackId={stats.data?.top_track_id ?? null}
        placeholderRef={placeholderRef}
      />

      {isDwhEmpty && (
        <div className="glass-card rounded-xl mb-6" style={{ border: "1px solid rgba(29,185,84,0.15)" }}>
          <EmptyState title="Tu DWH está vacío" description="Ve a la página ETL y sincroniza tus datos de Spotify." showEtlLink />
        </div>
      )}

      <div className="mb-4">
        <QuickStatsCards stats={stats.data ?? null} loading={stats.loading} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <HeroSection />
        <TopArtistsSection artists={artists.data?.artists?.slice(0, 5) ?? []} loading={artists.loading} />
        <TopTracksSection tracks={tracks.data?.tracks?.slice(0, 5) ?? []} loading={tracks.loading} />
        <GenresSection topGenres={genres.data?.genres?.slice(0, 5) ?? []} loading={genres.loading} />
        <MinutesSection totalMinutes={Math.round(stats.data?.total_minutes ?? 0)} loading={stats.loading} />
        <FavoriteSongSection stats={stats.data ?? null} loading={stats.loading} placeholderRef={placeholderRef} />
        <PeakHourSection />
        <ExplorerSection
          totalArtists={stats.data?.total_artists ?? 0}
          totalPlays={stats.data?.total_plays ?? 0}
          loading={stats.loading}
        />
        <SearchSection />
        <ThanksSection />
      </div>
    </AppLayout>
  );
}
