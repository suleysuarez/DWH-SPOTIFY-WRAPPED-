/**
 * Wrapped.tsx — Resumen del historial: minutos, artista y canción favoritos y hora pico.
 * Datos de GET /v1/history/wrapped. La hora pico llega en UTC y se muestra en hora local.
 */

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import AppLayout from "@/components/layout/AppLayout";
import EmptyState from "@/components/ui/EmptyState";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import { formatHour, toLocalHour } from "@/lib/time";
import type { WrappedSummary } from "@/types/history";

function Card({ label, delay, children }: { label: string; delay: number; children: ReactNode }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="rounded-2xl p-6 flex flex-col gap-3"
      style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(29,185,84,0.2)" }}
    >
      <p className="text-xs uppercase tracking-widest text-white/60">{label}</p>
      {children}
    </motion.section>
  );
}

function Cover({ src, alt, round }: { src: string | null; alt: string; round?: boolean }) {
  const shape = round ? "rounded-full" : "rounded-xl";
  return src ? (
    <img src={src} alt={alt} className={`w-28 h-28 object-cover ${shape}`} />
  ) : (
    <div className={`w-28 h-28 flex items-center justify-center text-3xl text-[#1DB954] bg-[#1DB954]/10 ${shape}`}>♪</div>
  );
}

export default function Wrapped() {
  const { data, loading, error } = useApi<WrappedSummary>(endpoints.history.wrapped);

  return (
    <AppLayout>
      <header className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl md:text-6xl font-black text-white">
            Tu <span className="text-[#1DB954]">Wrapped</span>
          </h1>
          {data?.first_play && data.last_play && (
            <p className="text-white/60 mt-2">
              Del {new Date(data.first_play).toLocaleDateString("es-CO")} al{" "}
              {new Date(data.last_play).toLocaleDateString("es-CO")} · {data.total_plays.toLocaleString("es-CO")}{" "}
              reproducciones
            </p>
          )}
        </div>
        <img src="/images/img_09.png" alt="" className="hidden md:block w-56 rounded-2xl" />
      </header>

      {loading && <p className="text-white/60">Cargando tu resumen...</p>}
      {!loading && error && <p className="text-red-400">No se pudo cargar el resumen. Intenta de nuevo.</p>}
      {!loading && !error && data && data.total_plays === 0 && (
        <EmptyState title="Aún no hay datos" description="Sincroniza tu historial desde la página ETL." showEtlLink />
      )}

      {!loading && data && data.total_plays > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card label="Minutos escuchados (estimados)" delay={0}>
            <p className="text-6xl font-black text-[#1DB954]">{data.total_minutes.toLocaleString("es-CO")}</p>
            <p className="text-white/60">Suma de la duración de cada canción reproducida.</p>
          </Card>

          <Card label="Tu hora pico" delay={0.1}>
            {data.peak_hour ? (
              <>
                <p className="text-6xl font-black text-white">{formatHour(toLocalHour(data.peak_hour.hour_utc))}</p>
                <p className="text-white/60">{data.peak_hour.play_count} reproducciones · hora local</p>
              </>
            ) : (
              <p className="text-white/60">Sin datos de hora.</p>
            )}
          </Card>

          {data.top_artist && (
            <Card label="Tu artista favorito" delay={0.2}>
              <div className="flex items-center gap-4">
                <Cover src={data.top_artist.image_url} alt={data.top_artist.name} round />
                <div className="min-w-0">
                  <p className="text-3xl font-black text-white break-words">{data.top_artist.name}</p>
                  <p className="text-white/60">
                    {data.top_artist.play_count} reproducciones · {data.top_artist.minutes} min
                  </p>
                </div>
              </div>
            </Card>
          )}

          {data.top_track && (
            <Card label="Tu canción favorita" delay={0.3}>
              <div className="flex items-center gap-4">
                <Cover src={data.top_track.image_url} alt={data.top_track.name} />
                <div className="min-w-0">
                  <p className="text-2xl font-black text-white break-words">{data.top_track.name}</p>
                  <p className="text-white/60">{data.top_track.artist_name}</p>
                  <p className="text-[#1DB954] font-bold">{data.top_track.play_count} veces</p>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}
    </AppLayout>
  );
}
