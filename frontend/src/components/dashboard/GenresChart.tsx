/**
 * GenresChart.tsx — Donut chart con top 5 géneros musicales.
 */

import type { GenreData } from "@/types/history";
import { Skeleton } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Headphones } from "lucide-react";

interface GenresChartProps {
  genres: GenreData[] | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

const COLORS = ["#1DB954", "#1ed760", "#17a349", "#148a3e", "#0f6b30"];
const GLOW_COLORS = [
  "rgba(29,185,84,0.6)",
  "rgba(30,215,96,0.5)",
  "rgba(23,163,73,0.5)",
  "rgba(20,138,62,0.4)",
  "rgba(15,107,48,0.4)",
];

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: GenreData & { percent: number } }>;
}) => {
  if (active && payload && payload.length) {
    const d = payload[0];
    return (
      <div
        className="rounded-xl px-4 py-3 text-xs"
        style={{
          background: "rgba(18,18,18,0.97)",
          border: "1px solid rgba(29,185,84,0.35)",
          boxShadow: "0 4px 24px rgba(29,185,84,0.15)",
          color: "#fff",
          backdropFilter: "blur(12px)",
        }}
      >
        <p className="font-bold capitalize text-sm mb-1">{d.payload.genre}</p>
        <p style={{ color: "#1DB954" }}>
          {d.value} reproducciones
        </p>
        <p style={{ color: "rgba(255,255,255,0.4)" }}>
          {(d.payload.percent * 100).toFixed(1)}% del total
        </p>
      </div>
    );
  }
  return null;
};

export default function GenresChart({
  genres,
  loading,
  error,
  onRetry,
}: GenresChartProps) {
  const top5 = genres?.slice(0, 5) ?? [];
  const total = top5.reduce((sum, g) => sum + g.count, 0);

  return (
    <div className="glass-card rounded-xl p-5" style={{ minHeight: 280 }}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "rgba(29,185,84,0.15)" }}
        >
          <Headphones className="w-4 h-4" style={{ color: "#1DB954" }} />
        </div>
        <div>
          <h3
            className="text-sm font-bold text-white"
            style={{ fontFamily: "DM Sans, sans-serif" }}
          >
            Géneros Dominantes
          </h3>
          <p className="text-xs text-white/40">Top 5 géneros</p>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex gap-6 mt-2">
          <Skeleton className="w-36 h-36 rounded-full flex-shrink-0" />
          <div className="space-y-3 flex-1 justify-center flex flex-col">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-2">
                <Skeleton className="w-3 h-3 rounded-full flex-shrink-0" />
                <Skeleton className="h-3 flex-1" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {!loading && error && <ErrorState message={error} onRetry={onRetry} />}

      {/* Empty */}
      {!loading && !error && top5.length === 0 && (
        <p className="text-sm text-white/30 mt-4">
          Sin datos de géneros disponibles.
        </p>
      )}

      {/* Chart */}
      {!loading && !error && top5.length > 0 && (
        <div className="flex items-center gap-4">
          {/* Donut */}
          <div className="relative flex-shrink-0" style={{ width: 160, height: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={top5}
                  cx="50%"
                  cy="50%"
                  innerRadius={48}
                  outerRadius={72}
                  dataKey="count"
                  paddingAngle={3}
                  startAngle={90}
                  endAngle={-270}
                >
                  {top5.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                      stroke="transparent"
                      style={{
                        filter: `drop-shadow(0 0 6px ${GLOW_COLORS[index % GLOW_COLORS.length]})`,
                      }}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Centro del donut */}
            <div
              className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
              style={{ top: 0 }}
            >
              <span className="text-xl font-bold text-white">{total}</span>
              <span className="text-xs text-white/40">plays</span>
            </div>
          </div>

          {/* Leyenda */}
          <div className="flex flex-col gap-2 flex-1 min-w-0">
            {top5.map((g, index) => {
              const pct = total > 0 ? Math.round((g.count / total) * 100) : 0;
              return (
                <div key={g.genre} className="flex items-center gap-2 min-w-0">
                  <span
                    className="flex-shrink-0 w-2.5 h-2.5 rounded-full"
                    style={{
                      background: COLORS[index % COLORS.length],
                      boxShadow: `0 0 6px ${GLOW_COLORS[index % GLOW_COLORS.length]}`,
                    }}
                  />
                  <span
                    className="capitalize text-xs text-white/80 truncate flex-1"
                    title={g.genre}
                  >
                    {g.genre}
                  </span>
                  <span className="text-xs font-semibold flex-shrink-0" style={{ color: "#1DB954" }}>
                    {pct}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
