/**
 * QuickStatsCards — KPI cards para el dashboard.
 * Muestra: artistas, canciones, reproducciones, minutos, cancion top.
 */
import { Skeleton } from "@/components/ui/SkeletonCard";
import { Users, Music, Play, Clock, Star } from "lucide-react";

interface QuickStats {
  total_tracks: number;
  total_artists: number;
  total_plays: number;
  total_minutes: number;
  last_sync: string | null;
  etl_status: string;
  top_track: string | null;
  top_track_artist: string | null;
  top_track_plays: number;
}

interface QuickStatsCardsProps {
  stats: QuickStats | null;
  loading: boolean;
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  accent = false,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div
      className="glass-card rounded-xl p-4 flex flex-col gap-2"
      style={{ border: accent ? "1px solid rgba(29,185,84,0.25)" : undefined }}
    >
      <div className="flex items-center gap-2">
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "rgba(29,185,84,0.12)" }}
        >
          <Icon className="w-3.5 h-3.5" style={{ color: "#1DB954" }} />
        </div>
        <span className="text-xs text-white/40 font-medium">{label}</span>
      </div>
      <div>
        <p
          className="text-xl font-black text-white truncate"
          style={{ fontFamily: "Nunito, sans-serif" }}
        >
          {value}
        </p>
        {sub && <p className="text-xs text-white/30 truncate mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default function QuickStatsCards({ stats, loading }: QuickStatsCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="glass-card rounded-xl p-4">
            <Skeleton className="h-4 w-20 mb-3" />
            <Skeleton className="h-7 w-16" />
          </div>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
      <StatCard
        icon={Users}
        label="Artistas"
        value={stats.total_artists}
        sub="únicos escuchados"
      />
      <StatCard
        icon={Music}
        label="Canciones"
        value={stats.total_tracks}
        sub="únicas escuchadas"
      />
      <StatCard
        icon={Play}
        label="Reproducciones"
        value={stats.total_plays}
        sub="en total"
      />
      <StatCard
        icon={Clock}
        label="Minutos"
        value={stats.total_minutes > 0 ? `${stats.total_minutes}` : "0"}
        sub="reproducidos"
      />
      <StatCard
        icon={Star}
        label="Más escuchada"
        value={stats.top_track ?? "—"}
        sub={
          stats.top_track
            ? `${stats.top_track_artist} · ${stats.top_track_plays}x`
            : "Sin datos aún"
        }
        accent
      />
    </div>
  );
}