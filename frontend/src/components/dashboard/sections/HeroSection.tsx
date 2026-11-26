import { motion } from "framer-motion";
import { Glow, Note, Num, P, PanelReveal, Stars } from "./shared";

export default function HeroSection() {
  const year = new Date().getFullYear();

  return (
    <PanelReveal>
      <div style={{ ...P, background: "linear-gradient(135deg,#060d06 0%,#0a1a0a 40%,#0e1628 100%)", border: "1px solid rgba(29,185,84,0.25)" }}>
        <Stars />
        <Num n="01" color="rgba(29,185,84,0.4)" />
        <Note style={{ top: 80, right: "48%" }} />
        <Note style={{ bottom: 120, left: "44%" }} />
        <Glow color="rgba(29,185,84,0.18)" style={{ left: -120, bottom: -120, width: 600, height: 600 }} />
        <Glow color="rgba(130,80,255,0.15)" style={{ right: "42%", top: -80, width: 400, height: 400 }} />

        <div style={{ position: "relative", zIndex: 2, flex: "0 0 50%", paddingRight: 40 }}>
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 28 }}
          >
            <img src="/images/logo_spotify.png" alt="Spotify" style={{ width: 28, height: 28, objectFit: "contain" }} />
            <span style={{ color: "#1DB954", fontWeight: 800, fontSize: 16 }}>Spotify</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22,1,0.36,1], delay: 0.1 }}
            style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(4rem,7vw,7rem)", fontWeight: 900, lineHeight: 0.95, letterSpacing: "-2px", marginBottom: 20 }}
          >
            <span style={{ color: "#fff" }}>Tu </span>
            <span style={{ color: "#1DB954", textShadow: "0 0 60px rgba(29,185,84,0.7)" }}>Wrapped</span><br />
            <span style={{ color: "rgba(255,255,255,0.85)" }}>{year}</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3, duration: 0.5 }}
            style={{ fontFamily: "DM Sans, sans-serif", fontWeight: 800, fontSize: 18, color: "rgba(255,255,255,0.75)", marginBottom: 8 }}
          >
            Suley Suárez &amp; Jhonatan Vera
          </motion.p>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4, duration: 0.5 }}
            style={{ fontSize: 15, color: "rgba(255,255,255,0.4)", lineHeight: 1.8, marginBottom: 36 }}
          >
            Un año. Mil historias.<br />Tu música, tu universo.
          </motion.p>
          <motion.a
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5, duration: 0.5 }}
            whileHover={{ scale: 1.04, boxShadow: "0 0 60px rgba(29,185,84,0.7)" }}
            href="/etl"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "#1DB954", color: "#000", padding: "14px 32px", borderRadius: 9999, fontWeight: 900, fontSize: 13, textDecoration: "none", boxShadow: "0 0 40px rgba(29,185,84,0.5)", letterSpacing: "0.05em" }}
          >
            SINCRONIZAR DATOS →
          </motion.a>
        </div>

        <motion.div
          initial={{ opacity: 0, x: 40 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          style={{ position: "absolute", right: 0, bottom: 0, top: 0, width: "50%", zIndex: 1 }}
        >
          <img src="/images/img_01.png" alt="" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "bottom right", filter: "drop-shadow(0 0 80px rgba(29,185,84,0.45)) drop-shadow(0 0 160px rgba(130,80,255,0.25))" }} />
        </motion.div>
      </div>
    </PanelReveal>
  );
}
