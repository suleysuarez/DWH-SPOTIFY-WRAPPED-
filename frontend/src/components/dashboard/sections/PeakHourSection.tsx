import PeakHourCard from "@/components/dashboard/PeakHourCard";
import { Glow, Num, P, PanelReveal, Stars } from "./shared";

export default function PeakHourSection() {
  return (
    <PanelReveal delay={0.05}>
      <div style={{ ...P, background: "linear-gradient(135deg,#060d06 0%,#0a1a0a 50%,#0d1f0d 100%)", border: "1px solid rgba(29,185,84,0.18)" }}>
        <Stars />
        <Num n="07" color="rgba(29,185,84,0.4)" />
        <Glow color="rgba(29,185,84,0.12)" style={{ left: -60, bottom: -60, width: 450, height: 450 }} />

        <div style={{ position: "relative", zIndex: 2, flex: "0 0 60%" }}>
          <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Tu actividad</h2>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#1DB954", marginBottom: 36 }}>por hora del día</p>
          <PeakHourCard />
        </div>

        {/* Foto decorativa: Suley */}
        <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: "42%", zIndex: 1, display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
          <img src="/images/suley.png" alt="Suley" style={{ height: "95%", width: "auto", objectFit: "contain", objectPosition: "center bottom", display: "block" }} />
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to right, #060d06 0%, transparent 30%), linear-gradient(to bottom, #060d06 0%, transparent 20%)" }} />
        </div>
      </div>
    </PanelReveal>
  );
}
