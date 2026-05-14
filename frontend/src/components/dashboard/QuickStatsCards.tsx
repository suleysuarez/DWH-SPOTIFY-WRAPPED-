/**
 * QuickStatsCards — 4 KPI cards: total tracks, artists, last sync, ETL status.
 */

import type { QuickStats } from "@/types/history";
import { Skeleton } from "@/components/ui/SkeletonCard";
import { Music, Users, RefreshCw, Activity } from "lucide-react";

interface QuickStatsCardsProps {
  stats: QuickStats | null;
  loading: boolean;
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  accent?: string;
}

function StatCard({ icon, label, value, accent = "#1DB954" }: StatCardProps) {
  return (
    <div
      className="glass-card rounded-xl p-4 flex items-center gap-4"
      style={{ transition: "transform 0.2s ease, box-shadow 0.2s ease" }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateY(-2px)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = `0 8px 32px rgba(29,185,84,0.12)`;
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
        (e.currentTarget as HTMLDivElement).style.boxShadow = "";
      }}
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
        style={{ background: `${accent}18` }}
      >
        <div style={{ color: accent }}>{icon}</div>
      </div>
      <div className="min-w-0">
        <p className="text-xs text-white/40 mb-0.5">{label}</p>
        <div className="text-lg font-black text-white" style={{ fontFamily: "Nunito, sans-serif" }}>
          {value}
        </div>
      </div>
    </div>
  );
}

const etlStatusColors: Record<string, string> = {
  idle: "#B3B3B3",
  running: "#FFA500",
  success: "#1DB954",
  error: "#EF4444",
};

const etlStatusLabels: Record<string, string> = {
  idle: "Inactivo",
  running: "Ejecutando",
  success: "Exitoso",
  error: "Error",
};

export default function QuickStatsCards({ stats, loading }: QuickStatsCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass-card rounded-xl p-4 flex items-center gap-4">
            <Skeleton className="w-10 h-10 rounded-xl flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-5 w-12" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const formatDate = (date: string | null) => {
    if (!date) return "—";
    try {
      return new Date(date).toLocaleDateString("es-UY", {
        day: "2-digit",
        month: "short",
      });
    } catch {
      return "—";
    }
  };

  const status = stats?.etl_status ?? "idle";

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        icon={<Music className="w-5 h-5" />}
        label="Total Canciones"
        value={stats?.total_tracks?.toLocaleString() ?? "—"}
      />
      <StatCard
        icon={<Users className="w-5 h-5" />}
        label="Total Artistas"
        value={stats?.total_artists?.toLocaleString() ?? "—"}
      />
      <StatCard
        icon={<RefreshCw className="w-5 h-5" />}
        label="Última Sincronización"
        value={formatDate(stats?.last_sync ?? null)}
        accent="#60A5FA"
      />
      <StatCard
        icon={<Activity className="w-5 h-5" />}
        label="Estado ETL"
        value={
          <span style={{ color: etlStatusColors[status] }}>
            {etlStatusLabels[status]}
          </span>
        }
        accent={etlStatusColors[status]}
      />
    </div>
  );
}
