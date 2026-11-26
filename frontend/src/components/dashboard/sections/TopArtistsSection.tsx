import { motion } from "framer-motion";
import Tilt3D from "@/components/ui/Tilt3D";
import { Glow, Note, Num, P, PanelReveal, Stars } from "./shared";
import type { TopArtistsResponse } from "@/types/artist";

export default function TopArtistsSection({ artists, loading }: { artists: TopArtistsResponse["artists"]; loading: boolean }) {
  return (
    <PanelReveal delay={0.05}>
      <div style={{ ...P, background: "linear-gradient(135deg,#060d06 0%,#0d1f0d 50%,#0a1a0a 100%)", border: "1px solid rgba(29,185,84,0.2)" }}>
        <Stars />
        <Num n="02" color="rgba(29,185,84,0.45)" />
        <Note style={{ top: 60, right: "48%" }} />
        <Glow color="rgba(29,185,84,0.15)" style={{ left: -80, top: -80, width: 500, height: 500 }} />

        <div style={{ position: "relative", zIndex: 2, flex: "0 0 52%", paddingRight: 60 }}>
          <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Tus artistas</h2>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#1DB954", marginBottom: 36 }}>más escuchados</p>

          {loading
            ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Cargando...</p>
            : artists.length === 0
              ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Sin datos aún. Ejecuta el ETL.</p>
              : artists.map((a, i) => (
                <Tilt3D
                  key={a.id}
                  intensity={8}
                  style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20, borderRadius: 14, padding: "8px 12px", background: "rgba(255,255,255,0.02)" }}
                >
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1, duration: 0.5 }}
                    style={{ display: "flex", alignItems: "center", gap: 16, width: "100%" }}
                  >
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
                  </motion.div>
                </Tilt3D>
              ))
          }
        </div>

        <div style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "48%", zIndex: 1 }}>
          <img src="/images/img_02.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right", filter: "drop-shadow(0 0 60px rgba(29,185,84,0.35))" }} />
        </div>
      </div>
    </PanelReveal>
  );
}
