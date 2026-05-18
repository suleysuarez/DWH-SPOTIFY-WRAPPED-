/**
 * Dashboard.tsx — Experiencia Spotify Wrapped: 9 paneles verticales full-screen.
 *
 * Todos los datos vienen del backend (sin datos inventados):
 *   GET /v1/artists/top           → top 5 artistas con imagen y reproducciones
 *   GET /v1/tracks/top            → top 5 canciones con imagen de álbum
 *   GET /v1/history/genres        → géneros con porcentaje calculado en Python
 *   GET /v1/history/peak-hour     → hora pico (PeakHourCard carga también distribución)
 *   GET /v1/history/stats         → total_minutes, total_plays, total_artists, top_track
 *
 * Panel 01: Hero presentación + img_01
 * Panel 02: Top artistas (play_count real = reproducciones) + img_02
 * Panel 03: Top canciones (album_image + play_count) + img_03
 * Panel 04: Géneros PieChart + lista porcentajes reales + img_04
 * Panel 05: Minutos escuchados (total_minutes real)
 * Panel 06: Canción favorita (top_track + top_track_artist + top_track_plays) + img_06
 * Panel 07: Hora pico — PeakHourCard (AreaChart + distribución 24h)
 * Panel 08: Explorador musical (total_artists únicos + total_plays) + img_08
 * Panel 09: Cierre + img_09
 *
 * Autoras/es: Suley Suárez y Jhonatan Vera — Universidad de Pamplona 2026-I
 */

import { useState } from "react";
import AppLayout from "@/components/layout/AppLayout";
import EmptyState from "@/components/ui/EmptyState";
import PeakHourCard from "@/components/dashboard/PeakHourCard";
import QuickStatsCards from "@/components/dashboard/QuickStatsCards";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import type { TopArtistsResponse } from "@/types/artist";
import type { TopTracksResponse } from "@/types/track";
import type { PeakHour, GenresResponse, QuickStats } from "@/types/history";
import { PieChart, Pie, Cell, ResponsiveContainer, Sector } from "recharts";

// ── Estrellas de fondo ────────────────────────────────────────────────────────
const STARS = Array.from({ length: 35 }, (_, i) => ({
  left: `${(i * 41 + 7) % 100}%`,
  top: `${(i * 67 + 13) % 100}%`,
  size: i % 4 === 0 ? 3 : i % 3 === 0 ? 2 : 1,
  opacity: 0.12 + (i % 6) * 0.07,
}));

function Stars() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {STARS.map((s, i) => (
        <div
          key={i}
          className="absolute rounded-full bg-white"
          style={{ left: s.left, top: s.top, width: s.size, height: s.size, opacity: s.opacity }}
        />
      ))}
    </div>
  );
}

// ── Helpers visuales ──────────────────────────────────────────────────────────
const GENRE_COLORS = ["#1DB954", "#17c3b2", "#4f8ef7", "#9b59b6", "#e91e8c"];
const GENRE_GLOWS  = ["rgba(29,185,84,0.7)", "rgba(23,195,178,0.7)", "rgba(79,142,247,0.7)", "rgba(155,89,182,0.7)", "rgba(233,30,140,0.7)"];

function Glow({ color, style }: { color: string; style?: React.CSSProperties }) {
  return (
    <div style={{
      position: "absolute", borderRadius: "50%", pointerEvents: "none",
      background: `radial-gradient(circle, ${color} 0%, transparent 65%)`,
      ...style,
    }} />
  );
}

function Num({ n, color = "rgba(255,255,255,0.15)" }: { n: string; color?: string }) {
  return (
    <div style={{
      position: "absolute", top: 28, right: 36,
      fontFamily: "DM Sans, sans-serif", fontSize: 16,
      fontWeight: 900, color, letterSpacing: 2,
    }}>{n}</div>
  );
}

function Note({ style }: { style?: React.CSSProperties }) {
  return (
    <span style={{ position: "absolute", fontSize: 22, opacity: 0.2, color: "#1DB954", pointerEvents: "none", ...style }}>
      ♪
    </span>
  );
}

// ── Estilo base de panel (full-screen) ────────────────────────────────────────
const P: React.CSSProperties = {
  position: "relative", overflow: "hidden", minHeight: "100vh", width: "100%",
  display: "flex", alignItems: "center", padding: "60px 8%", boxSizing: "border-box",
  borderRadius: 16,
};

// ── Panel 04: Géneros interactivo ─────────────────────────────────────────────
type GenreData = { genre: string; count: number; percentage: number };

function GenresPanel({ topGenres, loading }: { topGenres: GenreData[]; loading: boolean }) {
  const [activeIdx, setActiveIdx] = useState<number | null>(null);

  const active   = activeIdx !== null ? topGenres[activeIdx] : null;
  const activeColor = activeIdx !== null ? GENRE_COLORS[activeIdx % GENRE_COLORS.length] : GENRE_COLORS[0];
  const activeGlow  = activeIdx !== null ? GENRE_GLOWS[activeIdx  % GENRE_GLOWS.length]  : GENRE_GLOWS[0];
  const maxPct   = Math.max(...topGenres.map(g => g.percentage), 1);

  const renderActiveShape = (props: {
    cx: number; cy: number; innerRadius: number; outerRadius: number;
    startAngle: number; endAngle: number; fill: string;
  }) => {
    const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props;
    return (
      <g>
        <Sector cx={cx} cy={cy} innerRadius={innerRadius - 4} outerRadius={outerRadius + 16}
          startAngle={startAngle} endAngle={endAngle} fill={fill}
          style={{ filter: `drop-shadow(0 0 20px ${fill})` }} />
      </g>
    );
  };

  return (
    <div style={{ ...P, background: "linear-gradient(135deg,#07090f 0%,#0b1018 55%,#0e0818 100%)", border: "1px solid rgba(79,142,247,0.18)", flexDirection: "column", alignItems: "flex-start" }}>
      <Stars />
      <Num n="04" color="rgba(79,142,247,0.45)" />
      <Glow color="rgba(29,185,84,0.1)"   style={{ left: -100, bottom: -100, width: 600, height: 600 }} />
      <Glow color="rgba(79,142,247,0.08)" style={{ right: "30%", top: -80, width: 500, height: 500 }} />
      <Glow color="rgba(233,30,140,0.06)" style={{ right: -60, bottom: -60, width: 400, height: 400 }} />

      {/* Título */}
      <div style={{ position: "relative", zIndex: 2, marginBottom: 52 }}>
        <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4.2rem)", fontWeight: 900, color: "#fff", lineHeight: 1, marginBottom: 6 }}>Géneros</h2>
        <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(1.8rem,3vw,3rem)", fontWeight: 900, background: "linear-gradient(90deg,#1DB954,#17c3b2,#4f8ef7)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          que te definen
        </p>
      </div>

      <div style={{ position: "relative", zIndex: 2, display: "flex", alignItems: "center", gap: 80, width: "100%" }}>

        {/* Donut */}
        {!loading && topGenres.length > 0 && (
          <div style={{ position: "relative", flexShrink: 0, width: 400, height: 400 }}>
            {/* Anillo decorativo exterior */}
            <div style={{ position: "absolute", inset: -12, borderRadius: "50%", border: "1px solid rgba(255,255,255,0.04)", pointerEvents: "none" }} />

            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={topGenres}
                  dataKey="count"
                  cx="50%" cy="50%"
                  innerRadius={118} outerRadius={178}
                  paddingAngle={4}
                  startAngle={90} endAngle={-270}
                  activeIndex={activeIdx ?? undefined}
                  activeShape={renderActiveShape as never}
                  onMouseEnter={(_, idx) => setActiveIdx(idx)}
                  onMouseLeave={() => setActiveIdx(null)}
                  style={{ cursor: "pointer" }}
                >
                  {topGenres.map((_, i) => (
                    <Cell
                      key={i}
                      fill={GENRE_COLORS[i % GENRE_COLORS.length]}
                      stroke="rgba(7,9,15,0.6)"
                      strokeWidth={2}
                      opacity={activeIdx === null || activeIdx === i ? 1 : 0.25}
                      style={{ transition: "opacity 0.25s" }}
                    />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>

            {/* Centro */}
            <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
              {active ? (
                <>
                  <span style={{ fontFamily: "DM Sans, sans-serif", fontSize: 52, fontWeight: 900, color: activeColor, lineHeight: 1, textShadow: `0 0 40px ${activeGlow}` }}>
                    {active.percentage}%
                  </span>
                  <span style={{ fontSize: 15, color: "rgba(255,255,255,0.75)", marginTop: 10, textTransform: "capitalize", textAlign: "center", maxWidth: 140, fontWeight: 600 }}>
                    {active.genre}
                  </span>
                  <span style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", marginTop: 5 }}>
                    {active.count.toLocaleString()} plays
                  </span>
                </>
              ) : (
                <>
                  <span style={{ fontFamily: "DM Sans, sans-serif", fontSize: 52, fontWeight: 900, color: "#fff", lineHeight: 1 }}>
                    {topGenres.length}
                  </span>
                  <span style={{ fontSize: 13, color: "rgba(255,255,255,0.35)", marginTop: 8, letterSpacing: 2, textTransform: "uppercase" }}>géneros</span>
                </>
              )}
            </div>
          </div>
        )}

        {/* Lista */}
        {loading
          ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Cargando...</p>
          : topGenres.length === 0
            ? <p style={{ color: "rgba(255,255,255,0.3)", lineHeight: 1.8 }}>Sin géneros aún.<br />Ejecuta el ETL.</p>
            : (
              <div style={{ display: "flex", flexDirection: "column", gap: 20, flex: 1 }}>
                {topGenres.map((g, i) => {
                  const color = GENRE_COLORS[i % GENRE_COLORS.length];
                  const glow  = GENRE_GLOWS[i  % GENRE_GLOWS.length];
                  const isActive = activeIdx === i;
                  const barW = `${(g.percentage / maxPct) * 100}%`;
                  return (
                    <div
                      key={g.genre}
                      onMouseEnter={() => setActiveIdx(i)}
                      onMouseLeave={() => setActiveIdx(null)}
                      style={{ display: "flex", flexDirection: "column", gap: 8, cursor: "default", opacity: activeIdx === null || isActive ? 1 : 0.35, transition: "opacity 0.25s" }}
                    >
                      {/* Fila superior: nombre + porcentaje */}
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                          <span style={{
                            width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0,
                            boxShadow: isActive ? `0 0 16px ${glow}, 0 0 6px ${color}` : `0 0 4px ${color}55`,
                            transition: "box-shadow 0.25s"
                          }} />
                          <span style={{ fontSize: 17, color: isActive ? "#fff" : "rgba(255,255,255,0.6)", textTransform: "capitalize", fontWeight: isActive ? 700 : 400, transition: "color 0.25s, font-weight 0.25s" }}>
                            {g.genre}
                          </span>
                        </div>
                        <span style={{ fontFamily: "DM Sans, sans-serif", fontWeight: 900, fontSize: 20, color, textShadow: isActive ? `0 0 20px ${glow}` : "none", transition: "text-shadow 0.25s" }}>
                          {g.percentage}%
                        </span>
                      </div>
                      {/* Barra relativa al máximo */}
                      <div style={{ height: 6, background: "rgba(255,255,255,0.05)", borderRadius: 999, overflow: "hidden" }}>
                        <div style={{
                          width: barW, height: "100%", borderRadius: 999,
                          background: `linear-gradient(90deg, ${color}, ${color}99)`,
                          boxShadow: isActive ? `0 0 12px ${glow}` : "none",
                          transition: "box-shadow 0.25s"
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )
        }
      </div>

      <div style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "14%", zIndex: 1, opacity: 0.35 }}>
        <img src="/images/img_04.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right" }} />
      </div>
    </div>
  );
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function Dashboard() {
  const artists = useApi<TopArtistsResponse>(endpoints.artists.top);
  const tracks  = useApi<TopTracksResponse>(endpoints.tracks.top);
  const peakHour = useApi<PeakHour>(endpoints.history.peakHour);
  const genres  = useApi<GenresResponse>(endpoints.history.genres);
  const stats   = useApi<QuickStats>(endpoints.history.quickStats);

  const isDwhEmpty =
    !stats.loading && !stats.error && stats.data &&
    stats.data.total_tracks === 0 && stats.data.total_artists === 0;

  // Datos derivados — todos reales desde el backend
  const topArtists   = artists.data?.artists?.slice(0, 5) ?? [];
  const topTracks    = tracks.data?.tracks?.slice(0, 5) ?? [];
  const topGenres    = genres.data?.genres?.slice(0, 5) ?? [];
  const totalMinutes = Math.round(stats.data?.total_minutes ?? 0);
  const totalHours   = Math.round(totalMinutes / 60);
  const totalArtists = stats.data?.total_artists ?? 0;
  const totalPlays   = stats.data?.total_plays ?? 0;
  const topTrack     = stats.data?.top_track ?? null;
  const topTrackArtist = stats.data?.top_track_artist ?? null;
  const topTrackPlays  = stats.data?.top_track_plays ?? 0;

  const year = new Date().getFullYear();

  return (
    <AppLayout>
      {isDwhEmpty && (
        <div className="glass-card rounded-xl mb-6" style={{ border: "1px solid rgba(29,185,84,0.15)" }}>
          <EmptyState
            title="Tu DWH está vacío"
            description="Ve a la página ETL y sincroniza tus datos de Spotify."
            showEtlLink
          />
        </div>
      )}

      <div className="mb-4">
        <QuickStatsCards stats={stats.data ?? null} loading={stats.loading} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

        {/* ══ 01 HERO ══════════════════════════════════════════════════════════ */}
        <div style={{ ...P, background: "linear-gradient(135deg,#060d06 0%,#0a1a0a 40%,#0e1628 100%)", border: "1px solid rgba(29,185,84,0.25)" }}>
          <Stars />
          <Num n="01" color="rgba(29,185,84,0.4)" />
          <Note style={{ top: 80, right: "48%" }} />
          <Note style={{ bottom: 120, left: "44%" }} />
          <Glow color="rgba(29,185,84,0.18)" style={{ left: -120, bottom: -120, width: 600, height: 600 }} />
          <Glow color="rgba(130,80,255,0.15)" style={{ right: "42%", top: -80, width: 400, height: 400 }} />

          <div style={{ position: "relative", zIndex: 2, flex: "0 0 50%", paddingRight: 40 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 28 }}>
              <img src="/images/logo_spotify.png" alt="Spotify" style={{ width: 28, height: 28, objectFit: "contain" }} />
              <span style={{ color: "#1DB954", fontWeight: 800, fontSize: 16 }}>Spotify</span>
            </div>
            <h1 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(4rem,7vw,7rem)", fontWeight: 900, lineHeight: 0.95, letterSpacing: "-2px", marginBottom: 20 }}>
              <span style={{ color: "#fff" }}>Tu </span>
              <span style={{ color: "#1DB954", textShadow: "0 0 60px rgba(29,185,84,0.7)" }}>Wrapped</span><br />
              <span style={{ color: "rgba(255,255,255,0.85)" }}>{year}</span>
            </h1>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontWeight: 800, fontSize: 18, color: "rgba(255,255,255,0.75)", marginBottom: 8 }}>
              Suley Suárez &amp; Jhonatan Vera
            </p>
            <p style={{ fontSize: 15, color: "rgba(255,255,255,0.4)", lineHeight: 1.8, marginBottom: 36 }}>
              Un año. Mil historias.<br />Tu música, tu universo.
            </p>
            <a
              href="/etl"
              style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "#1DB954", color: "#000", padding: "14px 32px", borderRadius: 9999, fontWeight: 900, fontSize: 13, textDecoration: "none", boxShadow: "0 0 40px rgba(29,185,84,0.5)", letterSpacing: "0.05em" }}
            >
              SINCRONIZAR DATOS →
            </a>
          </div>

          <div style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "50%", zIndex: 1 }}>
            <img src="/images/img_01.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right", filter: "drop-shadow(0 0 80px rgba(29,185,84,0.45)) drop-shadow(0 0 160px rgba(130,80,255,0.25))" }} />
          </div>
        </div>

        {/* ══ 02 TOP ARTISTAS ══════════════════════════════════════════════════ */}
        <div style={{ ...P, background: "linear-gradient(135deg,#060d06 0%,#0d1f0d 50%,#0a1a0a 100%)", border: "1px solid rgba(29,185,84,0.2)" }}>
          <Stars />
          <Num n="02" color="rgba(29,185,84,0.45)" />
          <Note style={{ top: 60, right: "48%" }} />
          <Glow color="rgba(29,185,84,0.15)" style={{ left: -80, top: -80, width: 500, height: 500 }} />

          <div style={{ position: "relative", zIndex: 2, flex: "0 0 52%", paddingRight: 60 }}>
            <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Tus artistas</h2>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#1DB954", marginBottom: 36 }}>más escuchados</p>

            {artists.loading
              ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Cargando...</p>
              : topArtists.length === 0
                ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Sin datos aún. Ejecuta el ETL.</p>
                : topArtists.map((a, i) => (
                  <div key={a.id} style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
                    <span style={{ fontFamily: "DM Sans, sans-serif", fontWeight: 900, fontSize: 15, color: "#1DB954", width: 28 }}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    {a.images?.[0]?.url
                      ? <img src={a.images[0].url} alt={a.name} style={{ width: 44, height: 44, borderRadius: "50%", objectFit: "cover", border: "2px solid rgba(29,185,84,0.3)" }} />
                      : <div style={{ width: 44, height: 44, borderRadius: "50%", background: "rgba(29,185,84,0.1)", display: "flex", alignItems: "center", justifyContent: "center", color: "#1DB954", fontSize: 16 }}>♪</div>}
                    <div>
                      <p style={{ fontSize: 17, fontWeight: 800, color: "#fff" }}>{a.name}</p>
                      <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
                        {a.play_count ? `${a.play_count.toLocaleString()} reproducciones` : a.genres?.[0] ?? ""}
                      </p>
                    </div>
                  </div>
                ))
            }
          </div>

          <div style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "48%", zIndex: 1 }}>
            <img src="/images/img_02.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right", filter: "drop-shadow(0 0 60px rgba(29,185,84,0.35))" }} />
          </div>
        </div>

        {/* ══ 03 TOP CANCIONES ════════════════════════════════════════════════ */}
        <div style={{ ...P, background: "linear-gradient(135deg,#0d0a1a 0%,#1a0a2e 50%,#0f0f1a 100%)", border: "1px solid rgba(167,139,250,0.2)" }}>
          <Stars />
          <Num n="03" color="rgba(167,139,250,0.5)" />
          <Note style={{ top: 60, left: "48%", color: "#a78bfa" }} />
          <Glow color="rgba(167,139,250,0.14)" style={{ right: "45%", bottom: -80, width: 480, height: 480 }} />

          <div style={{ position: "absolute", left: 0, bottom: 0, top: 0, width: "46%", zIndex: 1 }}>
            <img src="/images/img_03.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom left", filter: "drop-shadow(0 0 60px rgba(167,139,250,0.3))" }} />
          </div>

          <div style={{ position: "relative", zIndex: 2, marginLeft: "50%", paddingLeft: 20 }}>
            <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Tus canciones</h2>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#a78bfa", marginBottom: 36 }}>más escuchadas</p>

            {tracks.loading
              ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Cargando...</p>
              : topTracks.length === 0
                ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Sin datos aún. Ejecuta el ETL.</p>
                : topTracks.map((t, i) => (
                  <div key={t.id} style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
                    <span style={{ fontFamily: "DM Sans, sans-serif", fontWeight: 900, fontSize: 15, color: "#a78bfa", width: 28 }}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    {t.album_image
                      ? <img src={t.album_image} alt={t.name} style={{ width: 44, height: 44, borderRadius: 8, objectFit: "cover", border: "2px solid rgba(167,139,250,0.3)" }} />
                      : <div style={{ width: 44, height: 44, borderRadius: 8, background: "rgba(167,139,250,0.1)", display: "flex", alignItems: "center", justifyContent: "center", color: "#a78bfa", fontSize: 16 }}>♪</div>}
                    <div style={{ minWidth: 0 }}>
                      <p style={{ fontSize: 17, fontWeight: 800, color: "#fff", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.name}</p>
                      <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
                        {t.play_count ? `${t.play_count} reproducciones` : t.artist_name}
                      </p>
                    </div>
                  </div>
                ))
            }
          </div>
        </div>

        {/* ══ 04 GÉNEROS ══════════════════════════════════════════════════════ */}
        <GenresPanel topGenres={topGenres} loading={genres.loading} />

        {/* ══ 05 MINUTOS ══════════════════════════════════════════════════════ */}
        <div style={{ ...P, background: "linear-gradient(135deg,#0a0a12 0%,#181028 50%,#0f0f1a 100%)", border: "1px solid rgba(167,139,250,0.18)" }}>
          <Stars />
          <Num n="05" color="rgba(167,139,250,0.45)" />
          <Note style={{ top: 60, right: "46%", color: "#a78bfa" }} />
          <Glow color="rgba(130,80,255,0.15)" style={{ right: -60, top: -60, width: 500, height: 500 }} />
          <Glow color="rgba(29,185,84,0.10)" style={{ left: -60, bottom: -60, width: 400, height: 400 }} />

          <div style={{ position: "relative", zIndex: 2, flex: "0 0 55%" }}>
            <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Minutos</h2>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#a78bfa", marginBottom: 40 }}>escuchados</p>

            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(4rem,8vw,8rem)", fontWeight: 900, lineHeight: 1, color: "#1DB954", marginBottom: 8, textShadow: "0 0 80px rgba(29,185,84,0.6)" }}>
              {stats.loading ? "..." : totalMinutes.toLocaleString()}
            </p>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 26, fontWeight: 700, color: "rgba(255,255,255,0.7)", marginBottom: 20 }}>minutos</p>
            <p style={{ fontSize: 16, color: "rgba(255,255,255,0.35)", lineHeight: 1.8 }}>
              {stats.loading ? "" : `Equivalente a ${totalHours.toLocaleString()} horas\nde música pura.`}
            </p>
          </div>
        </div>

        {/* ══ 06 CANCIÓN FAVORITA ══════════════════════════════════════════════ */}
        <div style={{ ...P, background: "linear-gradient(135deg,#0a0a0a 0%,#0d1520 50%,#0a0f0a 100%)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <Stars />
          <Num n="06" />
          <Note style={{ top: 60, left: "48%" }} />
          <Glow color="rgba(29,185,84,0.12)" style={{ right: 40, top: 40, width: 400, height: 400 }} />

          <div style={{ position: "relative", zIndex: 2, flex: "0 0 52%", paddingRight: 40 }}>
            <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Tu canción</h2>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#1DB954", marginBottom: 40 }}>favorita</p>

            {stats.loading
              ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Cargando...</p>
              : topTrack
                ? (
                  <>
                    <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(1.8rem,3vw,2.8rem)", fontWeight: 900, color: "#fff", lineHeight: 1.2, marginBottom: 12, textShadow: "0 0 40px rgba(29,185,84,0.4)" }}>
                      {topTrack}
                    </p>
                    <p style={{ fontSize: 18, color: "rgba(255,255,255,0.5)", marginBottom: 24 }}>{topTrackArtist}</p>
                    <div style={{ display: "inline-flex", alignItems: "center", gap: 10, background: "rgba(29,185,84,0.1)", border: "1px solid rgba(29,185,84,0.25)", borderRadius: 12, padding: "12px 22px" }}>
                      <span style={{ fontSize: 24 }}>🎵</span>
                      <div>
                        <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", marginBottom: 2 }}>la pusiste</p>
                        <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 20, fontWeight: 900, color: "#1DB954" }}>
                          {topTrackPlays.toLocaleString()} veces
                        </p>
                      </div>
                    </div>
                  </>
                )
                : <p style={{ color: "rgba(255,255,255,0.3)" }}>Sin datos aún. Ejecuta el ETL.</p>
            }
          </div>

          <div style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "44%", zIndex: 1 }}>
            <img src="/images/img_06.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right", filter: "drop-shadow(0 0 60px rgba(29,185,84,0.3))", opacity: 0.85 }} />
          </div>
        </div>

        {/* ══ 07 HORA PICO ════════════════════════════════════════════════════ */}
        <div style={{ ...P, background: "linear-gradient(135deg,#060d06 0%,#0a1a0a 50%,#0d1f0d 100%)", border: "1px solid rgba(29,185,84,0.18)" }}>
          <Stars />
          <Num n="07" color="rgba(29,185,84,0.4)" />
          <Glow color="rgba(29,185,84,0.12)" style={{ left: -60, bottom: -60, width: 450, height: 450 }} />

          <div style={{ position: "relative", zIndex: 2, width: "100%" }}>
            <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Tu actividad</h2>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#1DB954", marginBottom: 36 }}>por hora del día</p>
            <div style={{ maxWidth: 800 }}>
              <PeakHourCard
                data={peakHour.data}
                loading={peakHour.loading}
                error={peakHour.error}
                onRetry={peakHour.refetch}
              />
            </div>
          </div>
        </div>

        {/* ══ 08 EXPLORADOR ════════════════════════════════════════════════════ */}
        <div style={{ ...P, background: "linear-gradient(135deg,#0a0a0a 0%,#0f0a1a 50%,#0a0f1a 100%)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <Stars />
          <Num n="08" />
          <Note style={{ top: 60, right: "46%" }} />
          <Glow color="rgba(130,80,255,0.13)" style={{ left: -60, top: -60, width: 450, height: 450 }} />

          <div style={{ position: "relative", zIndex: 2, flex: "0 0 52%", paddingRight: 40 }}>
            <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Explorador</h2>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#1DB954", marginBottom: 48 }}>musical</p>

            <p style={{ fontSize: 18, color: "rgba(255,255,255,0.6)", marginBottom: 12 }}>Escuchaste</p>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(4rem,7vw,7rem)", fontWeight: 900, lineHeight: 1, color: "#fff", marginBottom: 8 }}>
              {stats.loading ? "..." : totalArtists.toLocaleString()}
            </p>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 24, fontWeight: 700, color: "rgba(255,255,255,0.5)", marginBottom: 32 }}>artistas únicos</p>

            <div style={{ display: "inline-flex", alignItems: "center", gap: 12, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 14, padding: "14px 24px" }}>
              <span style={{ fontSize: 20 }}>🎵</span>
              <span style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", lineHeight: 1.6 }}>
                {stats.loading ? "..." : `${totalPlays.toLocaleString()} reproducciones`}<br />en tu historial
              </span>
            </div>
          </div>

          <div style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "44%", zIndex: 1 }}>
            <img src="/images/img_08.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right", filter: "drop-shadow(0 0 60px rgba(130,80,255,0.3))", opacity: 0.85 }} />
          </div>
        </div>

        {/* ══ 09 GRACIAS ══════════════════════════════════════════════════════ */}
        <div style={{ ...P, background: "linear-gradient(135deg,#060d06 0%,#0a1a0a 40%,#0e1628 100%)", border: "1px solid rgba(29,185,84,0.25)" }}>
          <Stars />
          <Num n="09" color="rgba(29,185,84,0.4)" />
          <Note style={{ top: 60, right: "48%" }} />
          <Glow color="rgba(29,185,84,0.18)" style={{ right: -80, bottom: -80, width: 600, height: 600 }} />
          <Glow color="rgba(130,80,255,0.12)" style={{ left: -60, top: -60, width: 400, height: 400 }} />

          <div style={{ position: "relative", zIndex: 2, flex: "0 0 50%", paddingRight: 40 }}>
            <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,5vw,5rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Gracias por</h2>
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,5vw,5rem)", fontWeight: 900, color: "#1DB954", marginBottom: 32, textShadow: "0 0 60px rgba(29,185,84,0.6)" }}>escuchar</p>
            <p style={{ fontSize: 17, color: "rgba(255,255,255,0.45)", lineHeight: 1.9, marginBottom: 48 }}>
              La música nos conecta.<br />Gracias por hacer de este<br />año algo inolvidable.
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <img src="/images/logo_spotify.png" alt="Spotify" style={{ width: 36, height: 36, objectFit: "contain" }} />
              <div>
                <p style={{ fontSize: 18, fontWeight: 900, color: "#fff" }}>Spotify</p>
                <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>Escuchar es todo</p>
              </div>
            </div>
          </div>

          <div style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "50%", zIndex: 1 }}>
            <img src="/images/img_09.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right", filter: "drop-shadow(0 0 60px rgba(29,185,84,0.4))", opacity: 0.85 }} />
          </div>
        </div>

      </div>
    </AppLayout>
  );
}
