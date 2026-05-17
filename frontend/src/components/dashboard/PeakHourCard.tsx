/**
 * PeakHourCard.tsx — Gráfico de área con distribución de reproducciones por hora.
 *
 * Recibe la hora pico desde el padre (Dashboard) vía props, y carga
 * independientemente la distribución completa (24h) en su propio useEffect
 * desde GET /v1/history/peak-hour/distribution.
 *
 * Props:
 *   data    → PeakHour | null  ({ hour, play_count, label })
 *   loading → boolean          (para la hora pico del padre)
 *   error   → string | null
 *   onRetry → () => void
 *
 * El gráfico usa Recharts AreaChart con gradiente verde Spotify.
 * Una ReferenceLine vertical marca la hora pico.
 * El eje X muestra solo cada 3 horas para evitar solapamiento.
 *
 * Nota: usa `VITE_API_BASE_URL` (no `VITE_API_URL`) como fallback 127.0.0.1:8000.
 * Esta inconsistencia existe respecto al resto de componentes que usan lib/api.ts.
 */
import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart, ReferenceLine } from "recharts";
import type { PeakHour } from "@/types/history";
import { Skeleton } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import { Clock } from "lucide-react";
import { getToken } from "@/lib/auth";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

interface HourPoint { hour: number; play_count: number; label: string; }

interface PeakHourCardProps {
  data: PeakHour | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as HourPoint;
  return (
    <div style={{
      background: "rgba(10,10,10,0.92)",
      border: "1px solid rgba(29,185,84,0.3)",
      borderRadius: 8,
      padding: "8px 12px",
    }}>
      <p style={{ color: "#1DB954", fontWeight: 700, fontSize: 13 }}>{d.label}</p>
      <p style={{ color: "rgba(255,255,255,0.7)", fontSize: 12 }}>{d.play_count} reproducciones</p>
    </div>
  );
};

export default function PeakHourCard({ data, loading, error, onRetry }: PeakHourCardProps) {
  const [hours, setHours] = useState<HourPoint[]>([]);
  const [loadingDist, setLoadingDist] = useState(true);

  useEffect(() => {
    const fetchDist = async () => {
      try {
        const token = getToken();
        const res = await fetch(`${API_BASE}/v1/history/peak-hour/distribution`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const json = await res.json();
        setHours(json.hours ?? []);
      } catch { } finally {
        setLoadingDist(false);
      }
    };
    fetchDist();
  }, []);

  const peakHour = data?.hour ?? null;
  const maxCount = Math.max(...hours.map(h => h.play_count), 1);

  // Solo mostrar label cada 3 horas en el eje X
  const xLabels = ["00", "03", "06", "09", "12", "15", "18", "21"];

  return (
    <div className="glass-card rounded-xl p-5 flex flex-col" style={{ minHeight: 260 }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "rgba(29,185,84,0.15)" }}>
            <Clock className="w-4 h-4" style={{ color: "#1DB954" }} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white" style={{ fontFamily: "DM Sans, sans-serif" }}>
              Actividad por Hora
            </h3>
            <p className="text-xs text-white/40">Reproducciones a lo largo del día</p>
          </div>
        </div>
        {data && !loading && (
          <div className="text-right">
            <p className="text-xs text-white/40">Hora pico</p>
            <p className="text-lg font-black" style={{ color: "#1DB954", fontFamily: "DM Sans, sans-serif" }}>
              {String(data.hour).padStart(2, "0")}:00
            </p>
          </div>
        )}
      </div>

      {/* States */}
      {(loading || loadingDist) && (
        <div className="space-y-2 flex-1">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      )}
      {!loading && !loadingDist && error && <ErrorState message={error} onRetry={onRetry} />}
      {!loading && !loadingDist && !error && hours.length === 0 && (
        <p className="text-sm text-white/30 mt-2">Sin datos disponibles</p>
      )}

      {/* Chart */}
      {!loading && !loadingDist && !error && hours.length > 0 && (
        <div style={{ flex: 1, minHeight: 160 }}>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={hours} margin={{ top: 8, right: 4, left: -28, bottom: 0 }}>
              <defs>
                <linearGradient id="peakGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1DB954" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#1DB954" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="label"
                tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                interval={2}
              />
              <YAxis
                tick={{ fill: "rgba(255,255,255,0.25)", fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(29,185,84,0.2)", strokeWidth: 1 }} />
              {peakHour !== null && (
                <ReferenceLine
                  x={String(peakHour).padStart(2, "0") + ":00"}
                  stroke="rgba(29,185,84,0.5)"
                  strokeDasharray="3 3"
                  label={{ value: "pico", fill: "rgba(29,185,84,0.7)", fontSize: 9, position: "top" }}
                />
              )}
              <Area
                type="monotone"
                dataKey="play_count"
                stroke="#1DB954"
                strokeWidth={2}
                fill="url(#peakGrad)"
                dot={false}
                activeDot={{ r: 4, fill: "#1DB954", stroke: "#000", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Footer stat */}
      {!loading && !loadingDist && data && (
        <p className="text-xs text-white/30 mt-2">
          {data.play_count.toLocaleString()} reproducciones en la hora pico
        </p>
      )}
    </div>
  );
}