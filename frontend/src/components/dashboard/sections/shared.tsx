/** Piezas visuales compartidas por las secciones del Dashboard. */
import { motion } from "framer-motion";
import { useCountUp } from "@/hooks/useCountUp";

// ── Stars ─────────────────────────────────────────────────────────────────────
const STARS = Array.from({ length: 35 }, (_, i) => ({
  left: `${(i * 41 + 7) % 100}%`,
  top: `${(i * 67 + 13) % 100}%`,
  size: i % 4 === 0 ? 3 : i % 3 === 0 ? 2 : 1,
  opacity: 0.12 + (i % 6) * 0.07,
}));

export function Stars() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {STARS.map((s, i) => (
        <div key={i} className="absolute rounded-full bg-white"
          style={{ left: s.left, top: s.top, width: s.size, height: s.size, opacity: s.opacity }} />
      ))}
    </div>
  );
}

// ── PanelReveal — scroll-triggered entrance ───────────────────────────────────
export function PanelReveal({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 56 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay }}
    >
      {children}
    </motion.div>
  );
}

// ── AnimatedNumber — counts up when scrolled into view ────────────────────────
export function AnimatedNumber({ value, style }: { value: number; style?: React.CSSProperties }) {
  const [count, ref] = useCountUp(value);
  return (
    <span ref={ref} style={style}>
      {count.toLocaleString()}
    </span>
  );
}

// ── Helpers visuales ──────────────────────────────────────────────────────────

export function Glow({ color, style }: { color: string; style?: React.CSSProperties }) {
  return (
    <div style={{
      position: "absolute", borderRadius: "50%", pointerEvents: "none",
      background: `radial-gradient(circle, ${color} 0%, transparent 65%)`,
      ...style,
    }} />
  );
}

export function Num({ n, color = "rgba(255,255,255,0.15)" }: { n: string; color?: string }) {
  return (
    <div style={{
      position: "absolute", top: 28, right: 36,
      fontFamily: "DM Sans, sans-serif", fontSize: 16,
      fontWeight: 900, color, letterSpacing: 2,
    }}>{n}</div>
  );
}

export function Note({ style }: { style?: React.CSSProperties }) {
  return (
    <span style={{ position: "absolute", fontSize: 22, opacity: 0.2, color: "#1DB954", pointerEvents: "none", ...style }}>♪</span>
  );
}

export const P: React.CSSProperties = {
  position: "relative", overflow: "hidden", minHeight: "100vh", width: "100%",
  display: "flex", alignItems: "center", padding: "60px 8%", boxSizing: "border-box",
  borderRadius: 16,
};
