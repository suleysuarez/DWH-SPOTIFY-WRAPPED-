/**
 * GenresChart — horizontal bar chart showing top 5 genres.
 * Uses Recharts BarChart with custom Spotify green styling.
 */

import type { GenreData } from "@/types/history";
import { Skeleton } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Headphones } from "lucide-react";

interface GenresChartProps {
  genres: GenreData[] | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ value: number; payload: GenreData }> }) => {
  if (active && payload && payload.length) {
    const d = payload[0];
    return (
      <div
        className="rounded-lg px-3 py-2 text-xs"
        style={{
          background: "rgba(24,24,24,0.95)",
          border: "1px solid rgba(29,185,84,0.3)",
          color: "#fff",
        }}
      >
        <p className="font-semibold capitalize">{d.payload.genre}</p>
        <p style={{ color: "#1DB954" }}>{d.value} reproducciones</p>
      </div>
    );
  }
  return null;
};

export default function GenresChart({ genres, loading, error, onRetry }: GenresChartProps) {
  const top5 = genres?.slice(0, 5) ?? [];

  return (
    <div className="glass-card rounded-xl p-5" style={{ minHeight: 260 }}>
      <div className="flex items-center gap-2 mb-5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "rgba(29, 185, 84, 0.15)" }}
        >
          <Headphones className="w-4 h-4" style={{ color: "#1DB954" }} />
        </div>
        <div>
          <h3
            className="text-sm font-bold text-white"
            style={{ fontFamily: "Nunito, sans-serif" }}
          >
            Géneros Dominantes
          </h3>
          <p className="text-xs text-white/40">Top 5 géneros</p>
        </div>
      </div>

      {loading && (
        <div className="space-y-3 mt-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-3 w-24 flex-shrink-0" />
              <Skeleton className="h-5 flex-1" />
            </div>
          ))}
        </div>
      )}
      {!loading && error && <ErrorState message={error} onRetry={onRetry} />}
      {!loading && !error && top5.length === 0 && (
        <p className="text-sm text-white/30 mt-4">Sin datos de géneros disponibles.</p>
      )}
      {!loading && !error && top5.length > 0 && (
        <ResponsiveContainer width="100%" height={180}>
          <BarChart
            data={top5}
            layout="vertical"
            margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
          >
            <XAxis
              type="number"
              tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="genre"
              tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={90}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {top5.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={`rgba(29, 185, 84, ${1 - index * 0.15})`}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
