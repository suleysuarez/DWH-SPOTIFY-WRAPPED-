import type { RefObject } from "react";
import { motion } from "framer-motion";
import { AnimatedNumber, Glow, Note, Num, P, PanelReveal, Stars } from "./shared";
import type { QuickStats } from "@/types/history";

export default function FavoriteSongSection({ stats, loading, placeholderRef }: { stats: QuickStats | null; loading: boolean; placeholderRef: RefObject<HTMLDivElement | null> }) {
  const topTrack = stats?.top_track ?? null;
  const topTrackArtist = stats?.top_track_artist ?? null;
  const topTrackPlays = stats?.top_track_plays ?? 0;
  const topTrackId = stats?.top_track_id ?? null;
  const topTrackArtistImage = stats?.top_track_artist_image ?? null;

  return (
    <PanelReveal delay={0.05}>
      <div style={{ ...P, background: "linear-gradient(135deg,#070d07 0%,#0d1a0d 45%,#0a0f1a 100%)", border: "1px solid rgba(29,185,84,0.2)" }}>
        <Stars />
        <Num n="06" color="rgba(29,185,84,0.4)" />
        <Note style={{ top: 60, left: "48%" }} />
        <Glow color="rgba(29,185,84,0.14)" style={{ left: -80, bottom: -80, width: 500, height: 500 }} />
        <Glow color="rgba(130,80,255,0.08)" style={{ right: -40, top: -40, width: 400, height: 400 }} />

        {/* Columna izquierda: título + contador */}
        <div style={{ position: "relative", zIndex: 2, flex: "0 0 28%", paddingRight: 32 }}>
          <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.2rem,4vw,3.5rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Tu canción</h2>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(1.8rem,3.2vw,2.8rem)", fontWeight: 900, color: "#1DB954", marginBottom: 28 }}>favorita</p>
          {!loading && topTrack && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              style={{ display: "flex", flexDirection: "column", gap: 16 }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10, background: "rgba(29,185,84,0.08)", border: "1px solid rgba(29,185,84,0.18)", borderRadius: 12, padding: "12px 16px", width: "fit-content" }}>
                <span style={{ fontSize: 20 }}>🎵</span>
                <div>
                  <p style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginBottom: 2, letterSpacing: "0.08em", textTransform: "uppercase" }}>la pusiste</p>
                  <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 20, fontWeight: 900, color: "#1DB954", lineHeight: 1 }}>
                    <AnimatedNumber value={topTrackPlays} /> veces
                  </p>
                </div>
              </div>
              {topTrackId && (
                <motion.a
                  href={`https://open.spotify.com/track/${topTrackId}`}
                  target="_blank"
                  rel="noreferrer"
                  whileHover={{ scale: 1.04, boxShadow: "0 0 28px rgba(29,185,84,0.5)" }}
                  whileTap={{ scale: 0.97 }}
                  style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "#1DB954", color: "#000", padding: "10px 20px", borderRadius: 9999, fontWeight: 900, fontSize: 12, textDecoration: "none", boxShadow: "0 0 20px rgba(29,185,84,0.35)", letterSpacing: "0.04em", width: "fit-content" }}
                >
                  <img src="/images/logo_spotify.png" alt="" style={{ width: 14, height: 14, objectFit: "contain" }} />
                  ABRIR EN SPOTIFY
                </motion.a>
              )}
            </motion.div>
          )}
          {!loading && !topTrack && (
            <p style={{ color: "rgba(255,255,255,0.3)", fontSize: 14 }}>Sin datos aún. Ejecuta el ETL.</p>
          )}
        </div>

        {/* Tarjeta central glass: nombre + artista + embed */}
        {!loading && topTrack && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.94 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay: 0.12 }}
            style={{
              position: "relative", zIndex: 2,
              flex: "0 0 auto",
              display: "flex", flexDirection: "column", gap: 14,
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.09)",
              borderRadius: 22,
              padding: "22px 24px 24px",
              backdropFilter: "blur(8px)",
              boxShadow: "0 8px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06)",
              minWidth: 400,
            }}
          >
            {/* Nombre canción */}
            <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 18, fontWeight: 900, color: "#fff", lineHeight: 1.2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 400 }}>
              {topTrack}
            </p>

            {/* Chip artista */}
            <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 9999, padding: "5px 12px 5px 6px", width: "fit-content" }}>
              {topTrackArtistImage
                ? <img src={topTrackArtistImage} alt={topTrackArtist ?? ""} style={{ width: 24, height: 24, borderRadius: "50%", objectFit: "cover", border: "1px solid rgba(255,255,255,0.15)" }} />
                : <div style={{ width: 24, height: 24, borderRadius: "50%", background: "rgba(29,185,84,0.15)", display: "flex", alignItems: "center", justifyContent: "center", color: "#1DB954", fontSize: 11 }}>♪</div>
              }
              <span style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", fontWeight: 600 }}>{topTrackArtist}</span>
            </div>

            {/* Placeholder del iframe fijo — reserva el espacio */}
            {topTrackId && (
              <div
                ref={placeholderRef}
                style={{ width: 400, height: 152, borderRadius: 12, background: "rgba(29,185,84,0.03)", border: "1px solid rgba(29,185,84,0.08)" }}
              />
            )}
          </motion.div>
        )}

        {/* Video decorativo: Jhonatan */}
        <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, aspectRatio: "1 / 1", maxWidth: "42%", zIndex: 1, overflow: "hidden" }}>
          <video autoPlay loop muted playsInline style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}>
            <source src="/videos/jhon.mp4" type="video/mp4" />
          </video>
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to right, #070d07 0%, transparent 38%)" }} />
        </div>
      </div>
    </PanelReveal>
  );
}
