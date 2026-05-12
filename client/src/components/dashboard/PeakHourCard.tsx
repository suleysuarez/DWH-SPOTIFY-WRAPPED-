/**
 * PeakHourCard — displays the peak listening hour with a large time display.
 */

import type { PeakHour } from "@/types/history";
import { Skeleton } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import { Clock } from "lucide-react";

interface PeakHourCardProps {
  data: PeakHour | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export default function PeakHourCard({ data, loading, error, onRetry }: PeakHourCardProps) {
  const formatHour = (hour: number) => {
    const start = hour.toString().padStart(2, "0");
    const end = ((hour + 1) % 24).toString().padStart(2, "0");
    return `${start}:00 — ${end}:00`;
  };

  return (
    <div
      className="glass-card rounded-xl p-5 flex flex-col"
      style={{ minHeight: 160 }}
    >
      <div className="flex items-center gap-2 mb-4">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "rgba(29, 185, 84, 0.15)" }}
        >
          <Clock className="w-4 h-4" style={{ color: "#1DB954" }} />
        </div>
        <div>
          <h3
            className="text-sm font-bold text-white"
            style={{ fontFamily: "Nunito, sans-serif" }}
          >
            Hora Pico
          </h3>
          <p className="text-xs text-white/40">Mayor actividad</p>
        </div>
      </div>

      {loading && (
        <div className="space-y-2">
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      )}
      {!loading && error && <ErrorState message={error} onRetry={onRetry} />}
      {!loading && !error && !data && (
        <p className="text-sm text-white/30 mt-2">Sin datos disponibles</p>
      )}
      {!loading && !error && data && (
        <div className="mt-2">
          <p
            className="text-3xl font-black text-white tracking-tight"
            style={{ fontFamily: "Nunito, sans-serif", color: "#1DB954" }}
          >
            {formatHour(data.hour)}
          </p>
          <p className="text-xs text-white/40 mt-1">
            {data.play_count.toLocaleString()} reproducciones
          </p>
        </div>
      )}
    </div>
  );
}
