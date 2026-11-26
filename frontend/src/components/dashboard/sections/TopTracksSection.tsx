import { motion } from "framer-motion";
import Tilt3D from "@/components/ui/Tilt3D";
import { Glow, Note, Num, P, PanelReveal, Stars } from "./shared";
import type { TopTracksResponse } from "@/types/track";

export default function TopTracksSection({ tracks, loading }: { tracks: TopTracksResponse["tracks"]; loading: boolean }) {
  return (
    <PanelReveal delay={0.05}>
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

          {loading
            ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Cargando...</p>
            : tracks.length === 0
              ? <p style={{ color: "rgba(255,255,255,0.3)" }}>Sin datos aún. Ejecuta el ETL.</p>
              : tracks.map((t, i) => (
                <Tilt3D
                  key={t.id}
                  intensity={8}
                  style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20, borderRadius: 14, padding: "8px 12px", background: "rgba(255,255,255,0.02)" }}
                >
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1, duration: 0.5 }}
                    style={{ display: "flex", alignItems: "center", gap: 16, width: "100%", minWidth: 0 }}
                  >
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
                  </motion.div>
                </Tilt3D>
              ))
          }
        </div>
      </div>
    </PanelReveal>
  );
}
