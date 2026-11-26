/**
 * ConnectingScreen — Transición propia que se muestra antes de salir hacia Spotify.
 * No cubre ni imita las pantallas de Spotify: solo avisa qué va a pasar.
 */
import { motion } from "framer-motion";

export default function ConnectingScreen() {
  return (
    <motion.div
      role="status"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-6 px-6 text-center"
      style={{ background: "radial-gradient(circle at center, #0d1f0d 0%, #121212 70%)" }}
    >
      <motion.img
        src="/images/suley.png"
        alt=""
        className="w-48 h-48 object-contain rounded-full"
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
      />
      <p className="text-3xl font-black text-white">
        Te llevamos a <span style={{ color: "#1DB954" }}>Spotify</span>
      </p>
      <p className="max-w-md text-white/60 leading-relaxed">
        Spotify puede preguntarte si eres tú. Es su pantalla de seguridad: revisa que sea tu cuenta y continúa.
      </p>
      <div className="w-8 h-8 rounded-full border-2 border-white/10 border-t-[#1DB954] animate-spin" />
      <p className="text-xs text-white/30">La primera conexión puede tardar hasta un minuto.</p>
    </motion.div>
  );
}
