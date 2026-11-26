import { motion } from "framer-motion";
import { Glow, Note, Num, P, PanelReveal, Stars } from "./shared";

export default function ThanksSection() {
  return (
    <PanelReveal delay={0.05}>
      <div style={{ ...P, background: "linear-gradient(135deg,#060d06 0%,#0a1a0a 40%,#0e1628 100%)", border: "1px solid rgba(29,185,84,0.25)" }}>
        <Stars />
        <Num n="09" color="rgba(29,185,84,0.4)" />
        <Note style={{ top: 60, right: "48%" }} />
        <Glow color="rgba(29,185,84,0.18)" style={{ right: -80, bottom: -80, width: 600, height: 600 }} />
        <Glow color="rgba(130,80,255,0.12)" style={{ left: -60, top: -60, width: 400, height: 400 }} />

        <div style={{ position: "relative", zIndex: 2, flex: "0 0 50%", paddingRight: 40 }}>
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22,1,0.36,1] }}
            style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,5vw,5rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}
          >
            Gracias por
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7, ease: [0.22,1,0.36,1], delay: 0.1 }}
            style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,5vw,5rem)", fontWeight: 900, color: "#1DB954", marginBottom: 32, textShadow: "0 0 60px rgba(29,185,84,0.6)" }}
          >
            escuchar
          </motion.p>
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
    </PanelReveal>
  );
}
