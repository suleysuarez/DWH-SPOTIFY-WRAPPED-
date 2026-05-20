import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

const BACKEND_LOGIN_URL = "http://127.0.0.1:8000/v1/auth/login";

const EASE_OUT = [0.22, 1, 0.36, 1] as [number, number, number, number];

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.55, ease: EASE_OUT, delay },
});

function VideoPanel({ src, label, side }: { src: string; label: string; side: "left" | "right" }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: side === "left" ? -60 : 60 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.9, ease: EASE_OUT, delay: 0.1 }}
      className="relative flex-1 overflow-hidden"
    >
      <video
        src={src}
        autoPlay
        muted
        loop
        playsInline
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
      />

      {/* Gradient overlay — blends into center dark bg */}
      <div
        className="absolute inset-0"
        style={{
          background: side === "left"
            ? "linear-gradient(to right, rgba(18,18,18,0.25) 0%, rgba(18,18,18,0.7) 85%, rgba(18,18,18,1) 100%)"
            : "linear-gradient(to left,  rgba(18,18,18,0.25) 0%, rgba(18,18,18,0.7) 85%, rgba(18,18,18,1) 100%)",
        }}
      />

      {/* Subtle top/bottom fade */}
      <div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(to bottom, rgba(18,18,18,0.5) 0%, transparent 20%, transparent 80%, rgba(18,18,18,0.5) 100%)",
        }}
      />

      {/* Name label */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7, duration: 0.5 }}
        className="absolute bottom-8 w-full flex justify-center"
        style={{ [side === "left" ? "paddingRight" : "paddingLeft"]: "10%" }}
      >
        <span
          className="text-sm font-bold tracking-widest uppercase"
          style={{ color: "rgba(255,255,255,0.35)", letterSpacing: "0.2em" }}
        >
          {label}
        </span>
      </motion.div>

    </motion.div>
  );
}

export default function Login() {
  const handleConnect = async () => {
    const res = await fetch(BACKEND_LOGIN_URL);
    const data = await res.json();
    window.location.href = data.authorization_url;
  };

  return (
    <div
      className="h-screen flex overflow-hidden"
      style={{ background: "#121212" }}
    >
      {/* ── Video izquierdo — Suley ── */}
      <VideoPanel src="/videos/suley.mp4" label="Suley Suárez" side="left" />

      {/* ── Centro — Card ── */}
      <div className="relative z-10 flex items-center justify-center flex-shrink-0 w-[420px]">

        {/* Ambient glow detrás de la card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.6, ease: "easeOut" }}
          className="absolute rounded-full pointer-events-none"
          style={{
            width: 500, height: 500,
            background: "radial-gradient(circle, rgba(29,185,84,0.12) 0%, transparent 70%)",
            filter: "blur(50px)",
          }}
        />

        {/* Floating dots */}
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 + i * 0.1, duration: 0.6 }}
            className="absolute rounded-full pointer-events-none"
            style={{
              width: `${4 + (i % 3) * 2}px`,
              height: `${4 + (i % 3) * 2}px`,
              background: "rgba(29, 185, 84, 0.35)",
              top: `${20 + i * 12}%`,
              left: `${10 + i * 15}%`,
              animation: `floatDot${i % 3} ${5 + i}s ease-in-out infinite`,
              animationDelay: `${i * 0.8}s`,
            }}
          />
        ))}

        {/* Card */}
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
          className="relative w-full mx-4 rounded-2xl p-10 flex flex-col items-center text-center"
          style={{
            background: "rgba(20, 20, 20, 0.92)",
            backdropFilter: "blur(32px)",
            WebkitBackdropFilter: "blur(32px)",
            border: "1px solid rgba(255,255,255,0.09)",
            boxShadow: "0 32px 80px rgba(0,0,0,0.6), 0 0 80px rgba(29,185,84,0.1)",
          }}
        >
          <motion.img
            {...fadeUp(0.25)}
            src="/images/logo_spotify.png"
            alt="Spotify"
            className="w-20 h-20 object-contain mb-6"
          />

          <motion.h1
            {...fadeUp(0.35)}
            className="text-3xl font-black text-white mb-1 tracking-tight"
            style={{ fontFamily: "DM Sans, sans-serif" }}
          >
            Mi Spotify Wrapped
          </motion.h1>

          <motion.p {...fadeUp(0.42)} className="text-sm font-medium mb-2" style={{ color: "#1DB954" }}>
            Personal Data Warehouse
          </motion.p>

          <motion.p {...fadeUp(0.48)} className="text-sm text-white/40 mb-8 leading-relaxed">
            Conecta tu cuenta de Spotify para explorar tu historial musical y analíticas personales.
          </motion.p>

          <motion.div {...fadeUp(0.56)} className="w-full">
            <Button
              onClick={handleConnect}
              className="w-full h-12 text-base font-bold rounded-full gap-3 transition-all duration-200 active:scale-95"
              style={{
                background: "linear-gradient(135deg, #1DB954, #1ed760)",
                color: "#000",
                boxShadow: "0 4px 24px rgba(29,185,84,0.35)",
                fontFamily: "DM Sans, sans-serif",
              }}
              onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                e.currentTarget.style.boxShadow = "0 8px 36px rgba(29,185,84,0.55)";
                e.currentTarget.style.transform = "translateY(-2px) scale(1.01)";
              }}
              onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                e.currentTarget.style.boxShadow = "0 4px 24px rgba(29,185,84,0.35)";
                e.currentTarget.style.transform = "translateY(0) scale(1)";
              }}
            >
              <Sparkles className="w-4 h-4" />
              Conectar con Spotify
            </Button>
          </motion.div>

          <motion.p {...fadeUp(0.62)} className="text-xs text-white/25 mt-6">
            Al conectar, autorizas el acceso de lectura a tu historial de Spotify.
          </motion.p>
        </motion.div>
      </div>

      {/* ── Video derecho — Jhon ── */}
      <VideoPanel src="/videos/jhon.mp4" label="Jhonatan Vera" side="right" />

      <style>{`
        @keyframes floatDot0 {
          0%, 100% { transform: translateY(0); opacity: 0.3; }
          50% { transform: translateY(-12px); opacity: 0.8; }
        }
        @keyframes floatDot1 {
          0%, 100% { transform: translateY(0); opacity: 0.2; }
          50% { transform: translateY(-18px); opacity: 0.6; }
        }
        @keyframes floatDot2 {
          0%, 100% { transform: translateY(0); opacity: 0.4; }
          50% { transform: translateY(-8px); opacity: 0.9; }
        }
      `}</style>
    </div>
  );
}
