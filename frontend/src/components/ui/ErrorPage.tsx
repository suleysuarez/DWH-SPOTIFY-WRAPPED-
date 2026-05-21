import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useLocation } from "wouter";

interface ErrorPageProps {
  code: string;
  title: string;
  description: string;
  accentColor?: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}

const EASE = [0.22, 1, 0.36, 1] as [number, number, number, number];

// Waveform: todas las barras con altura fija, escalan desde el centro
const WAVE_COUNT = 28;
const WAVE_H = 56; // altura fija en px

// Patrones de escala pre-definidos (evitar Math.random() en render)
// Cada barra toma un patrón distinto → ondas asíncronas
const SCALE_PATTERNS: number[][] = [
  [0.12, 0.85, 0.3,  1,    0.45, 0.9,  0.2 ],
  [0.5,  0.15, 1,    0.35, 0.8,  0.2,  0.7 ],
  [0.8,  0.3,  0.6,  0.1,  0.95, 0.4,  0.75],
  [0.2,  1,    0.5,  0.75, 0.15, 0.9,  0.35],
  [0.65, 0.25, 0.9,  0.4,  0.1,  0.8,  0.55],
  [0.1,  0.7,  0.4,  0.9,  0.25, 0.6,  0.15],
  [0.9,  0.45, 0.15, 0.75, 0.5,  0.2,  1   ],
];

export default function ErrorPage({
  code,
  title,
  description,
  accentColor = "#1DB954",
  actionLabel = "Volver al inicio",
  actionHref = "/",
  onAction,
}: ErrorPageProps) {
  const [, setLocation] = useLocation();

  const handleAction = () => {
    if (onAction) onAction();
    else setLocation(actionHref);
  };

  const isLight = accentColor !== "#EF4444";

  return (
    <div style={{ minHeight: "100vh", background: "#121212", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", overflow: "hidden" }}>

      {/* Grid de fondo */}
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none",
        backgroundImage: `linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)`,
        backgroundSize: "60px 60px",
        maskImage: `radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%)`,
      }} />

      {/* Glow pulsante */}
      <motion.div
        animate={{ scale: [1, 1.12, 1], opacity: [0.7, 1, 0.7] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        style={{
          position: "absolute",
          width: 650,
          height: 650,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${accentColor}20 0%, transparent 65%)`,
          filter: "blur(55px)",
          pointerEvents: "none",
        }}
      />

      {/* Anillo decorativo */}
      <motion.div
        initial={{ opacity: 0, scale: 0.6 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, ease: EASE, delay: 0.1 }}
        style={{
          position: "absolute",
          width: 480,
          height: 480,
          borderRadius: "50%",
          border: `1px solid ${accentColor}18`,
          pointerEvents: "none",
        }}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.6 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, ease: EASE, delay: 0.2 }}
        style={{
          position: "absolute",
          width: 340,
          height: 340,
          borderRadius: "50%",
          border: `1px solid ${accentColor}12`,
          pointerEvents: "none",
        }}
      />

      {/* Dots flotantes */}
      {[
        { s: 5, t: "13%", l: "8%" }, { s: 7, t: "20%", l: "83%" },
        { s: 4, t: "70%", l: "7%" }, { s: 6, t: "76%", l: "87%" },
        { s: 8, t: "44%", l: "3%" }, { s: 4, t: "56%", l: "94%" },
      ].map((d, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.15, 0.6, 0.15] }}
          transition={{ delay: i * 0.2, duration: 3.5 + i * 0.6, repeat: Infinity, ease: "easeInOut" }}
          style={{ position: "absolute", width: d.s, height: d.s, borderRadius: "50%", background: accentColor, top: d.t, left: d.l }}
        />
      ))}

      {/* Contenido */}
      <div style={{ position: "relative", zIndex: 1, textAlign: "center", padding: "48px 32px", display: "flex", flexDirection: "column", alignItems: "center" }}>

        {/* Logo Spotify */}
        <motion.img
          src="/images/logo_spotify.png"
          alt="Spotify"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 0.5, y: 0 }}
          transition={{ duration: 0.6, ease: EASE }}
          style={{ width: 36, height: 36, objectFit: "contain", marginBottom: 32 }}
        />

        {/* Número de error */}
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.82 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.75, ease: EASE, delay: 0.1 }}
          style={{
            fontFamily: "DM Sans, sans-serif",
            fontSize: "clamp(6.5rem, 17vw, 12rem)",
            fontWeight: 900,
            lineHeight: 1,
            color: accentColor,
            textShadow: `0 0 60px ${accentColor}50, 0 0 120px ${accentColor}28`,
            letterSpacing: "-0.05em",
            marginBottom: 4,
            userSelect: "none",
          }}
        >
          {code}
        </motion.div>

        {/* Onda musical — barras desde el centro, misma altura, escalan simétricamente */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          style={{ display: "flex", alignItems: "center", gap: 3, height: WAVE_H + 8, marginBottom: 28 }}
        >
          {Array.from({ length: WAVE_COUNT }).map((_, i) => {
            const pattern = SCALE_PATTERNS[i % SCALE_PATTERNS.length];
            // Barras centrales más activas, extremos más suaves
            const centerFactor = 1 - Math.abs((i - WAVE_COUNT / 2) / (WAVE_COUNT / 2)) * 0.45;
            const scaledPattern = pattern.map(v => Math.max(0.08, v * centerFactor));
            return (
              <motion.div
                key={i}
                animate={{ scaleY: scaledPattern }}
                transition={{
                  duration: 0.9 + (i % 5) * 0.18,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: i * 0.055,
                  repeatType: "mirror",
                }}
                style={{
                  width: 3,
                  height: WAVE_H,
                  background: accentColor,
                  borderRadius: 99,
                  transformOrigin: "center", // pulsa hacia arriba Y hacia abajo
                  opacity: 0.82,
                  flexShrink: 0,
                }}
              />
            );
          })}
        </motion.div>

        {/* Título */}
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: EASE, delay: 0.3 }}
          style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(1.3rem, 3vw, 1.85rem)", fontWeight: 800, color: "#fff", marginBottom: 10 }}
        >
          {title}
        </motion.h2>

        {/* Descripción */}
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE, delay: 0.38 }}
          style={{ fontSize: 14, color: "rgba(255,255,255,0.38)", marginBottom: 36, maxWidth: 360, lineHeight: 1.7 }}
        >
          {description}
        </motion.p>

        {/* Botón */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: EASE, delay: 0.46 }}
          whileHover={{ scale: 1.04, boxShadow: `0 8px 36px ${accentColor}55` }}
          whileTap={{ scale: 0.97 }}
        >
          <Button
            onClick={handleAction}
            style={{
              background: `linear-gradient(135deg, ${accentColor}, ${accentColor}cc)`,
              color: isLight ? "#000" : "#fff",
              fontWeight: 800,
              borderRadius: 9999,
              padding: "12px 40px",
              fontSize: 14,
              fontFamily: "DM Sans, sans-serif",
              boxShadow: `0 4px 28px ${accentColor}45`,
              border: "none",
              letterSpacing: "0.01em",
            }}
          >
            {actionLabel}
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
