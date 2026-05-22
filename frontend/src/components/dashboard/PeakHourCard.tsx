/**
 * PeakHourCard.tsx — Gráfico de área con distribución de reproducciones por hora.
 *
 * Componente autónomo: gestiona sus propias llamadas a API con selector de período.
 * Períodos disponibles: Día (1d), Semana (7d), Mes (30d), Todo.
 *
 * El gráfico usa Recharts AreaChart con gradiente verde Spotify.
 * Una ReferenceLine vertical marca la hora pico.
 */
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Skeleton } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import { Clock } from "lucide-react";
import { getToken } from "@/lib/auth";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

type Period = "day" | "week" | "month" | "all";

interface HourPoint { hour: number; play_count: number; label: string; }
interface PeakHour { hour: number; play_count: number; label: string; }

const PERIODS: { key: Period; label: string }[] = [
  { key: "day",   label: "Día"    },
  { key: "week",  label: "Semana" },
  { key: "month", label: "Mes"    },
  { key: "all",   label: "Todo"   },
];

// Patrones de altura para las barras musicales (igual que el 404)
const BAR_PATTERNS: number[][] = [
  [0.2, 0.9, 0.4, 1,   0.3],
  [0.6, 0.2, 1,   0.5, 0.8],
  [0.3, 0.7, 0.2, 0.9, 0.5],
  [0.8, 0.4, 0.7, 0.2, 1  ],
  [0.1, 1,   0.5, 0.8, 0.3],
];

function MusicBars({ active }: { active: boolean }) {
  const BAR_H = 18;
  const color = active ? "#1DB954" : "rgba(255,255,255,0.2)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 2, height: BAR_H + 4 }}>
      {Array.from({ length: 5 }).map((_, i) => {
        const pattern = BAR_PATTERNS[i % BAR_PATTERNS.length];
        return (
          <motion.div
            key={i}
            animate={active ? { scaleY: pattern } : { scaleY: 0.15 }}
            transition={active ? {
              duration: 0.7 + (i % 3) * 0.2,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.1,
              repeatType: "mirror",
            } : { duration: 0.3 }}
            style={{
              width: 3,
              height: BAR_H,
              background: color,
              borderRadius: 99,
              transformOrigin: "center",
              transition: "background 0.2s",
            }}
          />
        );
      })}
    </div>
  );
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

export default function PeakHourCard() {
  const [period, setPeriod] = useState<Period>("all");
  const [peak, setPeak] = useState<PeakHour | null>(null);
  const [hours, setHours] = useState<HourPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = getToken();
        const qs = period !== "all" ? `?period=${period}` : "";
        const headers = { Authorization: `Bearer ${token}` };
        const [peakRes, distRes] = await Promise.all([
          fetch(`${API_BASE}/v1/history/peak-hour${qs}`, { headers }),
          fetch(`${API_BASE}/v1/history/peak-hour/distribution${qs}`, { headers }),
        ]);
        if (!peakRes.ok || !distRes.ok) throw new Error("Error al cargar datos");
        const [peakJson, distJson] = await Promise.all([peakRes.json(), distRes.json()]);
        if (!cancelled) {
          setPeak(peakJson);
          setHours(distJson.hours ?? []);
        }
      } catch (e: any) {
        if (!cancelled) setError(e.message ?? "Error inesperado");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchData();
    return () => { cancelled = true; };
  }, [period]);

  const peakHour = peak?.hour ?? null;

  return (
    <div className="glass-card rounded-xl p-5 flex flex-col" style={{ minHeight: 260 }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
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
        {peak && !loading && (
          <div className="text-right">
            <p className="text-xs text-white/40">Hora pico</p>
            <p className="text-lg font-black" style={{ color: "#1DB954", fontFamily: "DM Sans, sans-serif" }}>
              {String(peak.hour).padStart(2, "0")}:00
            </p>
          </div>
        )}
      </div>

      {/* Period selector — barras musicales */}
      <div className="flex gap-2 mb-4">
        {PERIODS.map(p => {
          const active = period === p.key;
          return (
            <button
              key={p.key}
              type="button"
              onClick={() => setPeriod(p.key)}
              style={{
                flex: 1, display: "flex", flexDirection: "column", alignItems: "center",
                gap: 5, padding: "8px 4px", borderRadius: 12, cursor: "pointer",
                background: active ? "rgba(29,185,84,0.1)" : "rgba(255,255,255,0.04)",
                border: active ? "1px solid rgba(29,185,84,0.3)" : "1px solid rgba(255,255,255,0.06)",
                transition: "background 0.2s, border 0.2s",
              }}
            >
              <MusicBars active={active} />
              <span style={{
                fontSize: 10, fontWeight: 700, fontFamily: "DM Sans, sans-serif",
                color: active ? "#1DB954" : "rgba(255,255,255,0.35)",
                letterSpacing: "0.04em", transition: "color 0.2s",
              }}>
                {p.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* States */}
      {loading && (
        <div className="space-y-2 flex-1">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      )}
      {!loading && error && <ErrorState message={error} onRetry={() => setPeriod(period)} />}
      {!loading && !error && hours.length === 0 && (
        <p className="text-sm text-white/30 mt-2">Sin datos disponibles</p>
      )}

      {/* Chart */}
      {!loading && !error && hours.length > 0 && (
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
      {!loading && peak && (
        <p className="text-xs text-white/30 mt-2">
          {peak.play_count.toLocaleString()} reproducciones en la hora pico
        </p>
      )}
    </div>
  );
}
