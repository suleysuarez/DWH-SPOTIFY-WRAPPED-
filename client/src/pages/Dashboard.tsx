/**
 * Dashboard Page — main analytics view.
 * Calls: /v1/artists/top, /v1/tracks/top, /v1/history/peak-hour,
 *        /v1/history/genres, /v1/history/stats
 * Design: Glassmorphism Premium Dark
 */

import AppLayout from "@/components/layout/AppLayout";
import QuickStatsCards from "@/components/dashboard/QuickStatsCards";
import TopArtistsCard from "@/components/dashboard/TopArtistsCard";
import TopTracksCard from "@/components/dashboard/TopTracksCard";
import PeakHourCard from "@/components/dashboard/PeakHourCard";
import GenresChart from "@/components/dashboard/GenresChart";
import EmptyState from "@/components/ui/EmptyState";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import type { TopArtistsResponse } from "@/types/artist";
import type { TopTracksResponse } from "@/types/track";
import type { PeakHour, GenresResponse, QuickStats } from "@/types/history";

export default function Dashboard() {
  const artists = useApi<TopArtistsResponse>(endpoints.artists.top);
  const tracks = useApi<TopTracksResponse>(endpoints.tracks.top);
  const peakHour = useApi<PeakHour>(endpoints.history.peakHour);
  const genres = useApi<GenresResponse>(endpoints.history.genres);
  const stats = useApi<QuickStats>(endpoints.history.quickStats);

  // Determine if DWH is completely empty
  const isDwhEmpty =
    !stats.loading &&
    !stats.error &&
    stats.data &&
    stats.data.total_tracks === 0 &&
    stats.data.total_artists === 0;

  return (
    <AppLayout>
      {/* Welcome section */}
      <div className="mb-8">
        <h1
          className="text-3xl font-black text-white mb-1"
          style={{ fontFamily: "Nunito, sans-serif" }}
        >
          Dashboard
        </h1>
        <p className="text-sm text-white/40">
          Tu resumen personal de Spotify — datos desde tu Data Warehouse.
        </p>
      </div>

      {/* Empty DWH state */}
      {isDwhEmpty && (
        <div
          className="glass-card rounded-xl mb-8"
          style={{ border: "1px solid rgba(29,185,84,0.15)" }}
        >
          <EmptyState
            title="Tu DWH está vacío"
            description="Ve a la página ETL y sincroniza tus datos de Spotify."
            showEtlLink
          />
        </div>
      )}

      {/* KPI Cards */}
      <div className="mb-6">
        <QuickStatsCards stats={stats.data} loading={stats.loading} />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Top Artists */}
        <TopArtistsCard
          artists={artists.data?.artists ?? null}
          loading={artists.loading}
          error={artists.error}
          onRetry={artists.refetch}
        />

        {/* Top Tracks */}
        <TopTracksCard
          tracks={tracks.data?.tracks ?? null}
          loading={tracks.loading}
          error={tracks.error}
          onRetry={tracks.refetch}
        />

        {/* Right column: Peak Hour + Genres */}
        <div className="flex flex-col gap-6">
          <PeakHourCard
            data={peakHour.data}
            loading={peakHour.loading}
            error={peakHour.error}
            onRetry={peakHour.refetch}
          />
          <GenresChart
            genres={genres.data?.genres ?? null}
            loading={genres.loading}
            error={genres.error}
            onRetry={genres.refetch}
          />
        </div>
      </div>
    </AppLayout>
  );
}
