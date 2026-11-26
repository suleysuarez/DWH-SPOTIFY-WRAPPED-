import { AnimatedNumber, Glow, Note, Num, P, PanelReveal, Stars } from "./shared";

export default function MinutesSection({ totalMinutes, loading }: { totalMinutes: number; loading: boolean }) {
  const totalHours = Math.round(totalMinutes / 60);

  return (
    <PanelReveal delay={0.05}>
      <div style={{ ...P, background: "linear-gradient(135deg,#0a0a12 0%,#181028 50%,#0f0f1a 100%)", border: "1px solid rgba(167,139,250,0.18)" }}>
        <Stars />
        <Num n="05" color="rgba(167,139,250,0.45)" />
        <Note style={{ top: 60, right: "46%", color: "#a78bfa" }} />
        <Glow color="rgba(130,80,255,0.15)" style={{ right: -60, top: -60, width: 500, height: 500 }} />
        <Glow color="rgba(29,185,84,0.10)"  style={{ left: -60, bottom: -60, width: 400, height: 400 }} />

        <div style={{ position: "relative", zIndex: 2, flex: "0 0 55%" }}>
          <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Minutos</h2>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#a78bfa", marginBottom: 40 }}>escuchados</p>

          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(4rem,8vw,8rem)", fontWeight: 900, lineHeight: 1, color: "#1DB954", marginBottom: 8, textShadow: "0 0 80px rgba(29,185,84,0.6)" }}>
            {loading ? "..." : <AnimatedNumber value={totalMinutes} />}
          </p>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 26, fontWeight: 700, color: "rgba(255,255,255,0.7)", marginBottom: 20 }}>minutos</p>
          <p style={{ fontSize: 16, color: "rgba(255,255,255,0.35)", lineHeight: 1.8 }}>
            {loading ? "" : `Equivalente a ${totalHours.toLocaleString()} horas de música pura.`}
          </p>
        </div>

        {/* Video decorativo: DANCE */}
        <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: "65%", zIndex: 1, overflow: "hidden" }}>
          <video autoPlay loop muted playsInline style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "60% center" }}>
            <source src="/videos/DANCE.mp4" type="video/mp4" />
          </video>
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to right, #0a0a12 0%, transparent 35%), linear-gradient(to left, #0a0a12 0%, transparent 25%), linear-gradient(to bottom, #0a0a12 0%, transparent 25%), linear-gradient(to top, #0a0a12 0%, transparent 25%)" }} />
        </div>
      </div>
    </PanelReveal>
  );
}
