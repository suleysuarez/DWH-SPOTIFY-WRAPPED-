import Tilt3D from "@/components/ui/Tilt3D";
import { AnimatedNumber, Glow, Note, Num, P, PanelReveal, Stars } from "./shared";

export default function ExplorerSection({ totalArtists, totalPlays, loading }: { totalArtists: number; totalPlays: number; loading: boolean }) {
  return (
    <PanelReveal delay={0.05}>
      <div style={{ ...P, background: "linear-gradient(135deg,#0a0a0a 0%,#0f0a1a 50%,#0a0f1a 100%)", border: "1px solid rgba(255,255,255,0.07)" }}>
        <Stars />
        <Num n="08" />
        <Note style={{ top: 60, right: "46%" }} />
        <Glow color="rgba(130,80,255,0.13)" style={{ left: -60, top: -60, width: 450, height: 450 }} />

        <div style={{ position: "relative", zIndex: 2, flex: "0 0 52%", paddingRight: 40 }}>
          <h2 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2.5rem,4.5vw,4rem)", fontWeight: 900, color: "#fff", lineHeight: 1.05, marginBottom: 4 }}>Explorador</h2>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(2rem,3.5vw,3rem)", fontWeight: 900, color: "#1DB954", marginBottom: 48 }}>musical</p>

          <p style={{ fontSize: 18, color: "rgba(255,255,255,0.6)", marginBottom: 12 }}>Escuchaste</p>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(4rem,7vw,7rem)", fontWeight: 900, lineHeight: 1, color: "#fff", marginBottom: 8 }}>
            {loading ? "..." : <AnimatedNumber value={totalArtists} />}
          </p>
          <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 24, fontWeight: 700, color: "rgba(255,255,255,0.5)", marginBottom: 32 }}>artistas únicos</p>

          <Tilt3D intensity={5} style={{ display: "inline-flex", alignItems: "center", gap: 12, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 14, padding: "14px 24px", cursor: "default" }}>
            <span style={{ fontSize: 20 }}>🎵</span>
            <span style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", lineHeight: 1.6 }}>
              {loading ? "..." : <><AnimatedNumber value={totalPlays} /> reproducciones</>}<br />en tu historial
            </span>
          </Tilt3D>
        </div>

        {/* Video decorativo: piano */}
        <div style={{ position: "absolute", right: "1%", top: 0, bottom: 0, width: "60%", zIndex: 1, mixBlendMode: "screen", display: "flex", alignItems: "center" }}>
          <video autoPlay loop muted playsInline aria-hidden="true" style={{ width: "100%", aspectRatio: "16 / 9", objectFit: "contain", maskImage: "radial-gradient(ellipse 54% 54% at 50% 50%, #000 78%, transparent 100%)", WebkitMaskImage: "radial-gradient(ellipse 54% 54% at 50% 50%, #000 78%, transparent 100%)" }}>
            <source src="/videos/piano.mp4" type="video/mp4" />
          </video>
        </div>
      </div>
    </PanelReveal>
  );
}
