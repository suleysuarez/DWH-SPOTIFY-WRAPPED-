/** Reproductor de Spotify fijo, siempre montado para no cortar el audio. */
import { useEffect, useState, type RefObject } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function SpotifyFloatingPlayer({ topTrack, topTrackId, placeholderRef }: {
  topTrack: string | null;
  topTrackId: string | null;
  placeholderRef: RefObject<HTMLDivElement | null>;
}) {
  const [expanded, setExpanded] = useState(false);
  const [playerRect, setPlayerRect] = useState({ top: 0, left: 0, width: 380, height: 152 });
  const [rectReady, setRectReady] = useState(false);

  useEffect(() => {
    const sync = () => {
      if (!placeholderRef.current) return;
      const r = placeholderRef.current.getBoundingClientRect();
      setPlayerRect({ top: r.top, left: r.left, width: r.width, height: r.height });
      setRectReady(true);
    };
    const raf = requestAnimationFrame(sync);
    window.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", sync);
      window.removeEventListener("resize", sync);
    };
  }, [topTrack]);

  useEffect(() => {
    document.body.style.overflow = expanded ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [expanded]);

  if (!topTrackId || !rectReady) return null;

  return (
    <>
      <AnimatePresence>
        {expanded && (
          <motion.div
            key="player-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            onClick={() => setExpanded(false)}
            style={{ position: "fixed", inset: 0, zIndex: 9998, background: "rgba(0,0,0,0.82)", backdropFilter: "blur(14px)", WebkitBackdropFilter: "blur(14px)" }}
          />
        )}
      </AnimatePresence>

      <motion.div
        animate={expanded ? {
          x: (window.innerWidth  - 580) / 2,
          y: (window.innerHeight - 352) / 2,
          width:  580,
          height: 352,
        } : {
          x: playerRect.left,
          y: playerRect.top,
          width:  playerRect.width,
          height: playerRect.height,
        }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        style={{ position: "fixed", top: 0, left: 0, zIndex: expanded ? 9999 : 22, overflow: "visible" }}
      >
        {/* Iframe — recortado al border-radius */}
        <div style={{
          position: "absolute", inset: 0,
          borderRadius: expanded ? 20 : 14,
          overflow: "hidden",
          boxShadow: expanded
            ? "0 0 80px rgba(29,185,84,0.4), 0 30px 100px rgba(0,0,0,0.8)"
            : "0 0 28px rgba(29,185,84,0.22)",
        }}>
          <iframe
            title={`Reproducir ${topTrack ?? ""} en Spotify`}
            src={`https://open.spotify.com/embed/track/${topTrackId}?utm_source=generator&theme=0`}
            width="100%"
            height="100%"
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            style={{ display: "block", border: "none" }}
          />
          <AnimatePresence>
            {!expanded && (
              <motion.button
                key="expand-btn"
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.9 }}
                exit={{ opacity: 0 }}
                type="button"
                onClick={() => setExpanded(true)}
                title="Expandir reproductor"
                style={{ position: "absolute", bottom: 8, right: 8, background: "rgba(0,0,0,0.72)", border: "1px solid rgba(255,255,255,0.18)", color: "#fff", borderRadius: 7, padding: "6px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
              >
                <svg width="13" height="13" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M1 4.5V1H4.5M7.5 1H11V4.5M11 7.5V11H7.5M4.5 11H1V7.5"/>
                </svg>
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* Botón cerrar — fuera del overflow:hidden para sobresalir arriba */}
        <AnimatePresence>
          {expanded && (
            <motion.button
              key="close-btn"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ delay: 0.22 }}
              type="button"
              onClick={() => setExpanded(false)}
              style={{ position: "absolute", top: -46, right: 0, background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.22)", color: "#fff", borderRadius: 9999, padding: "10px 12px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
              title="Cerrar reproductor"
            >
              <svg width="14" height="14" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                <path d="M1 1l11 11M12 1L1 12"/>
              </svg>
            </motion.button>
          )}
        </AnimatePresence>
      </motion.div>
    </>
  );
}
