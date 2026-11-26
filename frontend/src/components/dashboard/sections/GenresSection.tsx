import { useState } from "react";
import { motion } from "framer-motion";
import { PieChart, Pie, Cell, ResponsiveContainer, Sector } from "recharts";
import Tilt3D from "@/components/ui/Tilt3D";
import { Glow, Num, P, PanelReveal, Stars } from "./shared";

const GENRE_COLORS = ["#1DB954", "#17c3b2", "#4f8ef7", "#9b59b6", "#e91e8c"];
const GENRE_GLOWS  = ["rgba(29,185,84,0.7)", "rgba(23,195,178,0.7)", "rgba(79,142,247,0.7)", "rgba(155,89,182,0.7)", "rgba(233,30,140,0.7)"];

// ── Géneros panel ─────────────────────────────────────────────────────────────
type GenreData = { genre: string; count: number; percentage: number };

export default function GenresSection({ topGenres, loading }: { topGenres: GenreData[]; loading: boolean }) {
  const [activeIdx, setActiveIdx] = useState<number | null>(null);
  const active      = activeIdx !== null ? topGenres[activeIdx] : null;
  const activeColor = activeIdx !== null ? GENRE_COLORS[activeIdx % GENRE_COLORS.length] : GENRE_COLORS[0];
  const activeGlow  = activeIdx !== null ? GENRE_GLOWS[activeIdx  % GENRE_GLOWS.length]  : GENRE_GLOWS[0];
  const maxPct      = Math.max(...topGenres.map(g => g.percentage), 1);

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
    <PanelReveal delay={0.05}>
    <div style={{ ...P, background: "linear-gradient(135deg,#07090f 0%,#0b1018 55%,#0e0818 100%)", border: "1px solid rgba(79,142,247,0.18)", flexDirection: "column", alignItems: "flex-start" }}>
      <Stars />
      <Num n="04" color="rgba(79,142,247,0.45)" />
      <Glow color="rgba(29,185,84,0.1)"   style={{ left: -100, bottom: -100, width: 600, height: 600 }} />
      <Glow color="rgba(79,142,247,0.08)" style={{ right: "30%", top: -80, width: 500, height: 500 }} />
      <Glow color="rgba(233,30,140,0.06)" style={{ right: -60, bottom: -60, width: 400, height: 400 }} />

      <div style={{ position: "relative", zIndex: 2, marginBottom: 52 }}>
        <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4.2rem)", fontWeight: 900, color: "#fff", lineHeight: 1, marginBottom: 6 }}>Géneros</h2>
        <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(1.8rem,3vw,3rem)", fontWeight: 900, background: "linear-gradient(90deg,#1DB954,#17c3b2,#4f8ef7)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          que te definen
        </p>
      </div>

      <div style={{ position: "relative", zIndex: 2, display: "flex", alignItems: "center", gap: 80, width: "56%" }}>
        {!loading && topGenres.length > 0 && (
          <Tilt3D intensity={6} style={{ position: "relative", flexShrink: 0, width: 400, height: 400 }}>
            <div style={{ position: "absolute", inset: -12, borderRadius: "50%", border: "1px solid rgba(255,255,255,0.04)", pointerEvents: "none" }} />
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={topGenres} dataKey="count" cx="50%" cy="50%"
                  innerRadius={118} outerRadius={178} paddingAngle={4}
                  startAngle={90} endAngle={-270}
                  activeIndex={activeIdx ?? undefined}
                  activeShape={renderActiveShape as never}
                  onMouseEnter={(_, idx) => setActiveIdx(idx)}
                  onMouseLeave={() => setActiveIdx(null)}
                  style={{ cursor: "pointer" }}
                >
                  {topGenres.map((_, i) => (
                    <Cell key={i} fill={GENRE_COLORS[i % GENRE_COLORS.length]}
                      stroke="rgba(7,9,15,0.6)" strokeWidth={2}
                      opacity={activeIdx === null || activeIdx === i ? 1 : 0.25}
                      style={{ transition: "opacity 0.25s" }} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
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
          </Tilt3D>
        )}

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
                  return (
                    <motion.div
                      key={g.genre}
                      initial={{ opacity: 0, x: 30 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.08, duration: 0.5, ease: "easeOut" }}
                      onMouseEnter={() => setActiveIdx(i)}
                      onMouseLeave={() => setActiveIdx(null)}
                      style={{ display: "flex", flexDirection: "column", gap: 8, cursor: "default", opacity: activeIdx === null || isActive ? 1 : 0.35, transition: "opacity 0.25s" }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                          <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0, boxShadow: isActive ? `0 0 16px ${glow}, 0 0 6px ${color}` : `0 0 4px ${color}55`, transition: "box-shadow 0.25s" }} />
                          <span style={{ fontSize: 17, color: isActive ? "#fff" : "rgba(255,255,255,0.6)", textTransform: "capitalize", fontWeight: isActive ? 700 : 400, transition: "color 0.25s, font-weight 0.25s" }}>
                            {g.genre}
                          </span>
                        </div>
                        <span style={{ fontFamily: "DM Sans, sans-serif", fontWeight: 900, fontSize: 20, color, textShadow: isActive ? `0 0 20px ${glow}` : "none", transition: "text-shadow 0.25s" }}>
                          {g.percentage}%
                        </span>
                      </div>
                      <div style={{ height: 6, background: "rgba(255,255,255,0.05)", borderRadius: 999, overflow: "hidden" }}>
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${(g.percentage / maxPct) * 100}%` }}
                          viewport={{ once: true }}
                          transition={{ delay: 0.3 + i * 0.1, duration: 0.8, ease: "easeOut" }}
                          style={{ height: "100%", borderRadius: 999, background: `linear-gradient(90deg, ${color}, ${color}99)`, boxShadow: isActive ? `0 0 12px ${glow}` : "none", transition: "box-shadow 0.25s" }}
                        />
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )
        }
      </div>

      <div style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "44%", zIndex: 1 }}>
        <img src="/images/img_04.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right", filter: "drop-shadow(0 0 60px rgba(79,142,247,0.35))", opacity: 0.85 }} />
      </div>
    </div>
    </PanelReveal>
  );
}
