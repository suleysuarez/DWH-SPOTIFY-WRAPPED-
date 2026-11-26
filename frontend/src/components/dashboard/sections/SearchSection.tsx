import SearchPanel from "@/components/dashboard/SearchPanel";
import { Glow, Num, P, PanelReveal, Stars } from "./shared";

export default function SearchSection() {
  return (
    <PanelReveal delay={0.05}>
      <div style={{ ...P, background: "linear-gradient(135deg,#08080f 0%,#0f0a1e 50%,#080f10 100%)", border: "1px solid rgba(130,80,255,0.18)" }}>
        <Stars />
        <Num n="09" color="rgba(130,80,255,0.45)" />
        <Glow color="rgba(130,80,255,0.12)" style={{ right: -60, top: -60, width: 500, height: 500 }} />
        <Glow color="rgba(29,185,84,0.08)"  style={{ left: -60, bottom: -60, width: 400, height: 400 }} />

        <div style={{ position: "relative", zIndex: 2, width: "100%" }}>
          <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Busca tu</h2>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#a78bfa", marginBottom: 36 }}>música favorita</p>
          <SearchPanel />
        </div>
      </div>
    </PanelReveal>
  );
}
