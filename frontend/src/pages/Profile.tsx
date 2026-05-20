import Navbar from "@/components/layout/Navbar";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import type { UserProfile } from "@/types/user";
import { SkeletonCard } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import Tilt3D from "@/components/ui/Tilt3D";
import { ExternalLink, Mail, Users, Crown, Star, Eye, EyeOff, MapPin } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

const EASE = [0.22, 1, 0.36, 1] as [number, number, number, number];
const fadeUp = (i: number) => ({
  initial: { opacity: 0, y: 22 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.55, ease: EASE, delay: 0.05 + i * 0.09 },
});

export default function Profile() {
  const { data: user, loading, error, refetch } = useApi<UserProfile>(endpoints.profile.me);
  const [showId, setShowId] = useState(false);

  const spotifyUrl = user?.spotify_id
    ? `https://open.spotify.com/user/${user.spotify_id}`
    : null;

  return (
    <div style={{ minHeight: "100vh", background: "#121212", display: "flex", flexDirection: "column" }}>
      <Navbar />

      {/* ── Split layout: info izquierda | video derecha ── */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

        {/* ══ IZQUIERDA: contenido scrollable ══════════════════════════════════ */}
        <div style={{ flex: 1, overflowY: "auto", padding: "40px 48px" }}>

          {loading && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <SkeletonCard className="h-52" />
              <SkeletonCard className="h-32" />
              <SkeletonCard className="h-32" />
            </div>
          )}

          {!loading && error && (
            <div className="glass-card rounded-xl p-8">
              <ErrorState message={error} onRetry={refetch} />
            </div>
          )}

          {!loading && !error && user && (
            <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>

              {/* ── Avatar + nombre ── */}
              <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
                <motion.div {...fadeUp(0)} style={{ position: "relative", flexShrink: 0 }}>
                  <div style={{
                    width: 180, height: 180, borderRadius: "50%", overflow: "hidden",
                    border: "4px solid #1DB954",
                    boxShadow: "0 0 50px rgba(29,185,84,0.55), 0 0 100px rgba(29,185,84,0.2)",
                  }}>
                    {user.image_url ? (
                      <img src={user.image_url} alt={user.display_name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    ) : (
                      <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(29,185,84,0.15)", color: "#1DB954", fontSize: 48, fontWeight: 900 }}>
                        {user.display_name?.charAt(0)?.toUpperCase() ?? "?"}
                      </div>
                    )}
                  </div>
                  {user.product === "premium" && (
                    <div style={{ position: "absolute", bottom: 6, right: 6, width: 38, height: 38, borderRadius: "50%", background: "#FFD700", boxShadow: "0 2px 14px rgba(255,215,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Crown style={{ width: 15, height: 15, color: "#000" }} />
                    </div>
                  )}
                </motion.div>

                <div>
                  <motion.h1 {...fadeUp(1)} style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(1.8rem, 3vw, 2.8rem)", fontWeight: 900, color: "#fff", lineHeight: 1.1, marginBottom: 12 }}>
                    {user.display_name || "—"}
                  </motion.h1>
                  <motion.div {...fadeUp(2)} style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <span style={user.product === "premium"
                      ? { fontSize: 12, fontWeight: 700, padding: "5px 14px", borderRadius: 9999, background: "rgba(255,215,0,0.15)", color: "#FFD700", border: "1px solid rgba(255,215,0,0.3)" }
                      : { fontSize: 12, fontWeight: 600, padding: "5px 14px", borderRadius: 9999, background: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.08)" }
                    }>
                      {user.product === "premium" ? "✦ Premium" : "Free"}
                    </span>
                    {user.country && (
                      <span style={{ fontSize: 12, fontWeight: 600, padding: "5px 14px", borderRadius: 9999, background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.08)", display: "flex", alignItems: "center", gap: 5 }}>
                        <MapPin style={{ width: 10, height: 10 }} />{user.country}
                      </span>
                    )}
                  </motion.div>
                </div>
              </div>

              {/* ── Seguidores destacado ── */}
              <motion.div {...fadeUp(3)} style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
                <span style={{ fontFamily: "DM Sans, sans-serif", fontSize: 56, fontWeight: 900, color: "#1DB954", lineHeight: 1, textShadow: "0 0 50px rgba(29,185,84,0.6)" }}>
                  {user.followers?.toLocaleString() ?? "0"}
                </span>
                <span style={{ fontSize: 15, color: "rgba(255,255,255,0.35)" }}>seguidores en Spotify</span>
              </motion.div>

              {/* ── Botón Spotify ── */}
              {spotifyUrl && (
                <motion.a
                  {...fadeUp(4)}
                  href={spotifyUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  whileHover={{ scale: 1.03, boxShadow: "0 0 40px rgba(29,185,84,0.5)" }}
                  style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "#1DB954", color: "#000", padding: "12px 28px", borderRadius: 9999, fontSize: 13, fontWeight: 900, textDecoration: "none", width: "fit-content", boxShadow: "0 4px 20px rgba(29,185,84,0.35)" }}
                >
                  <ExternalLink style={{ width: 14, height: 14 }} />
                  Ver en Spotify
                </motion.a>
              )}

              {/* ── Cards de datos ── */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>

                <motion.div {...fadeUp(5)}>
                  <Tilt3D intensity={7} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: "20px 22px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                      <div style={{ width: 32, height: 32, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(29,185,84,0.12)" }}>
                        <Mail style={{ width: 13, height: 13, color: "#1DB954" }} />
                      </div>
                      <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" }}>Email</span>
                    </div>
                    <p style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.75)" }}>{user.email || "—"}</p>
                  </Tilt3D>
                </motion.div>

                <motion.div {...fadeUp(6)}>
                  <Tilt3D intensity={7} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: "20px 22px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                      <div style={{ width: 32, height: 32, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", background: user.product === "premium" ? "rgba(255,215,0,0.12)" : "rgba(29,185,84,0.12)" }}>
                        {user.product === "premium"
                          ? <Crown style={{ width: 13, height: 13, color: "#FFD700" }} />
                          : <Star style={{ width: 13, height: 13, color: "#1DB954" }} />}
                      </div>
                      <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" }}>Plan</span>
                    </div>
                    <p style={{ fontSize: 15, fontWeight: 800, color: user.product === "premium" ? "#FFD700" : "rgba(255,255,255,0.55)" }}>
                      {user.product === "premium" ? "✦ Premium" : "Free"}
                    </p>
                  </Tilt3D>
                </motion.div>

                <motion.div {...fadeUp(7)}>
                  <Tilt3D intensity={7} style={{ background: "linear-gradient(135deg, rgba(29,185,84,0.1), rgba(29,185,84,0.03))", border: "1px solid rgba(29,185,84,0.22)", borderRadius: 16, padding: "20px 22px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                      <div style={{ width: 32, height: 32, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(29,185,84,0.15)" }}>
                        <Users style={{ width: 13, height: 13, color: "#1DB954" }} />
                      </div>
                      <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" }}>Seguidores</span>
                    </div>
                    <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 30, fontWeight: 900, color: "#1DB954", lineHeight: 1 }}>
                      {user.followers?.toLocaleString() ?? "0"}
                    </p>
                  </Tilt3D>
                </motion.div>

                <motion.div {...fadeUp(8)}>
                  <Tilt3D intensity={7} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 16, padding: "20px 22px" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{ width: 32, height: 32, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(255,255,255,0.06)" }}>
                          <span style={{ fontSize: 9, fontWeight: 900, color: "rgba(255,255,255,0.3)" }}>ID</span>
                        </div>
                        <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase" }}>Spotify ID</span>
                      </div>
                      <button type="button" onClick={() => setShowId(v => !v)} style={{ background: "none", border: "none", cursor: "pointer", color: "rgba(255,255,255,0.3)", display: "flex", padding: 0 }}>
                        {showId ? <EyeOff style={{ width: 13, height: 13 }} /> : <Eye style={{ width: 13, height: 13 }} />}
                      </button>
                    </div>
                    <p style={{ fontSize: 11, fontFamily: "monospace", color: "rgba(255,255,255,0.4)", wordBreak: "break-all", lineHeight: 1.6 }}>
                      {showId ? (user.spotify_id || "—") : "•".repeat(Math.min(user.spotify_id?.length ?? 8, 24))}
                    </p>
                  </Tilt3D>
                </motion.div>

              </div>
            </div>
          )}
        </div>

        {/* ══ DERECHA: video lateral fijo ══════════════════════════════════════ */}
        {/* Panel width = video height × (1080/1920) so portrait video fills without cropping */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
          style={{
            flexShrink: 0,
            width: "calc((100vh - 57px) * (1080 / 1920))",
            position: "sticky",
            top: 0,
            height: "calc(100vh - 57px)",
            overflow: "hidden",
            background: "#121212",
          }}
        >
          {/* Gradient fusion left edge */}
          <div style={{ position: "absolute", inset: 0, zIndex: 2, background: "linear-gradient(to right, #121212 0%, transparent 22%)" }} />
          {/* Top/bottom fade */}
          <div style={{ position: "absolute", inset: 0, zIndex: 2, background: "linear-gradient(to bottom, rgba(18,18,18,0.5) 0%, transparent 10%, transparent 90%, rgba(18,18,18,0.5) 100%)" }} />
          <video
            src="/videos/profile.mp4"
            autoPlay
            muted
            loop
            playsInline
            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
          />
        </motion.div>

      </div>
    </div>
  );
}
