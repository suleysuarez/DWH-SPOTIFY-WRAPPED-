import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { endpoints, ApiError } from "@/lib/api";
import type { EtlLogLine, EtlRunSummary, EtlTrackDetail, EtlHistoryDetail } from "@/types/etl";
import { Button } from "@/components/ui/button";
import { Play, RefreshCw, CheckCircle2, XCircle, Terminal, Info, AlertCircle, Disc3, History, SkipForward } from "lucide-react";
import { toast } from "sonner";

interface RunEtlPanelProps {
  onRunComplete?: () => void;
}

type RunStatus = "idle" | "running" | "success" | "error";
type SummaryTab = "new_tracks" | "history" | "skipped";

const LOG_ICONS: Record<EtlLogLine["type"], React.ReactNode> = {
  success: <CheckCircle2 className="w-3 h-3" />,
  error: <XCircle className="w-3 h-3" />,
  info: <Info className="w-3 h-3" />,
  warning: <AlertCircle className="w-3 h-3" />,
};

const LOG_COLORS: Record<EtlLogLine["type"], string> = {
  success: "#1DB954",
  error: "#EF4444",
  info: "rgba(255,255,255,0.6)",
  warning: "#FFA500",
};

function parseLogLine(raw: string): EtlLogLine {
  if (raw.toLowerCase().includes("success") || raw.toLowerCase().includes("loaded") || raw.toLowerCase().includes("obtained")) {
    return { type: "success", text: raw };
  }
  if (raw.toLowerCase().includes("error") || raw.toLowerCase().includes("failed")) {
    return { type: "error", text: raw };
  }
  if (raw.toLowerCase().includes("warn")) {
    return { type: "warning", text: raw };
  }
  return { type: "info", text: raw };
}

function formatPlayedAt(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es-CO", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

// ── Tarjeta de canción (nueva en catálogo o en historial) ────────────────────
function TrackRow({ image, name, sub, right }: { image?: string | null; name: string; sub: string; right?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
      {image
        ? <img src={image} alt={name} style={{ width: 36, height: 36, borderRadius: 6, objectFit: "cover", flexShrink: 0 }} />
        : <div style={{ width: 36, height: 36, borderRadius: 6, background: "rgba(29,185,84,0.1)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, color: "#1DB954", fontSize: 14 }}>♪</div>
      }
      <div style={{ minWidth: 0, flex: 1 }}>
        <p style={{ fontSize: 12, fontWeight: 700, color: "#fff", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{name}</p>
        <p style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{sub}</p>
      </div>
      {right && <span style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", flexShrink: 0 }}>{right}</span>}
    </div>
  );
}

// ── Panel de resumen post-ETL ────────────────────────────────────────────────
function SummaryPanel({ summary }: { summary: EtlRunSummary }) {
  const [tab, setTab] = useState<SummaryTab>("new_tracks");

  const tabs: { key: SummaryTab; icon: React.ReactNode; label: string; count: number; color: string }[] = [
    { key: "new_tracks",  icon: <Disc3 className="w-3.5 h-3.5" />,        label: "Nuevas en catálogo", count: summary.tracks_new,    color: "#1DB954" },
    { key: "history",     icon: <History className="w-3.5 h-3.5" />,      label: "Al historial",       count: summary.history_new,   color: "#4f8ef7" },
    { key: "skipped",     icon: <SkipForward className="w-3.5 h-3.5" />,  label: "Omitidas",           count: summary.history_skipped, color: "#F59E0B" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      style={{ marginTop: 16, borderRadius: 12, overflow: "hidden", border: "1px solid rgba(255,255,255,0.08)" }}
    >
      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
        {tabs.map(t => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            style={{
              flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 2,
              padding: "10px 8px", background: tab === t.key ? "rgba(255,255,255,0.05)" : "transparent",
              border: "none", cursor: "pointer",
              borderBottom: tab === t.key ? `2px solid ${t.color}` : "2px solid transparent",
              transition: "background 0.15s",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 5, color: tab === t.key ? t.color : "rgba(255,255,255,0.4)" }}>
              {t.icon}
              <span style={{ fontFamily: "DM Sans, sans-serif", fontWeight: 900, fontSize: 15, lineHeight: 1, color: tab === t.key ? "#fff" : "rgba(255,255,255,0.5)" }}>
                {t.count}
              </span>
            </div>
            <span style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", letterSpacing: "0.03em" }}>{t.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: "4px 14px 10px", maxHeight: 220, overflowY: "auto", background: "rgba(0,0,0,0.2)" }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, x: 6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -6 }}
            transition={{ duration: 0.18 }}
          >
            {tab === "new_tracks" && (
              summary.new_tracks.length === 0
                ? <p style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", padding: "14px 0", textAlign: "center" }}>
                    Ninguna canción nueva en el catálogo. Todo ya estaba sincronizado.
                  </p>
                : summary.new_tracks.map((t: EtlTrackDetail, i: number) => (
                  <TrackRow
                    key={i}
                    image={t.album_image_url}
                    name={t.name}
                    sub={[t.artist_name, t.album_name].filter(Boolean).join(" · ")}
                  />
                ))
            )}

            {tab === "history" && (
              summary.new_history.length === 0
                ? <p style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", padding: "14px 0", textAlign: "center" }}>
                    No se agregaron nuevas reproducciones al historial.
                  </p>
                : summary.new_history.map((h: EtlHistoryDetail, i: number) => (
                  <TrackRow
                    key={i}
                    image={h.album_image_url}
                    name={h.track_name}
                    sub={h.artist_name}
                    right={formatPlayedAt(h.played_at)}
                  />
                ))
            )}

            {tab === "skipped" && (
              <div style={{ padding: "14px 0" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)", borderRadius: 10, padding: "12px 14px" }}>
                  <SkipForward style={{ color: "#F59E0B", flexShrink: 0 }} size={20} />
                  <div>
                    <p style={{ fontSize: 13, fontWeight: 700, color: "#F59E0B", marginBottom: 3 }}>
                      {summary.history_skipped} {summary.history_skipped === 1 ? "reproducción omitida" : "reproducciones omitidas"}
                    </p>
                    <p style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", lineHeight: 1.6 }}>
                      Estas reproducciones ya existían en el historial (mismo timestamp). El pipeline las detectó como duplicados y las omitió correctamente.
                    </p>
                  </div>
                </div>
                {summary.tracks_updated > 0 && (
                  <div style={{ display: "flex", alignItems: "center", gap: 12, background: "rgba(79,142,247,0.08)", border: "1px solid rgba(79,142,247,0.2)", borderRadius: 10, padding: "12px 14px", marginTop: 10 }}>
                    <RefreshCw style={{ color: "#4f8ef7", flexShrink: 0 }} size={18} />
                    <div>
                      <p style={{ fontSize: 13, fontWeight: 700, color: "#4f8ef7", marginBottom: 3 }}>
                        {summary.tracks_updated} canciones actualizadas
                      </p>
                      <p style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", lineHeight: 1.6 }}>
                        Ya estaban en el catálogo. Se actualizaron sus metadatos (popularidad, portada, etc.).
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

// ── Componente principal ─────────────────────────────────────────────────────
export default function RunEtlPanel({ onRunComplete }: RunEtlPanelProps) {
  const [status, setStatus] = useState<RunStatus>("idle");
  const [logs, setLogs] = useState<EtlLogLine[]>([]);
  const [summary, setSummary] = useState<EtlRunSummary | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleRun = async () => {
    setStatus("running");
    setLogs([]);
    setSummary(null);
    setLogs([{ type: "info", text: "Iniciando proceso ETL..." }]);

    try {
      const result = await endpoints.etl.run();
      const parsedLogs: EtlLogLine[] = (result.logs ?? []).map(parseLogLine);

      for (let i = 0; i < parsedLogs.length; i++) {
        await new Promise((r) => setTimeout(r, 120));
        setLogs((prev) => [...prev, parsedLogs[i]]);
      }

      if (result.status === "success" || result.status === "started") {
        setLogs((prev) => [...prev, { type: "success", text: "ETL completado exitosamente." }]);
        setStatus("success");
        if (result.summary) setSummary(result.summary);
        toast.success("ETL completado", { description: "Datos sincronizados correctamente." });
        onRunComplete?.();
      } else {
        setLogs((prev) => [...prev, { type: "error", text: result.message ?? "ETL finalizó con errores." }]);
        setStatus("error");
        toast.error("ETL falló", { description: result.message });
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Error inesperado al ejecutar ETL.";
      setLogs((prev) => [...prev, { type: "error", text: message }]);
      setStatus("error");
      toast.error("Error ETL", { description: message });
    }
  };

  const handleReset = () => {
    setStatus("idle");
    setLogs([]);
    setSummary(null);
  };

  return (
    <div className="glass-card rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "rgba(29, 185, 84, 0.15)" }}>
            <Terminal className="w-4 h-4" style={{ color: "#1DB954" }} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white" style={{ fontFamily: "DM Sans, sans-serif" }}>Ejecutar ETL</h3>
            <p className="text-xs text-white/40">Sincronizar datos de Spotify</p>
          </div>
        </div>
        {status === "success" && (
          <div className="flex items-center gap-1.5 text-xs" style={{ color: "#1DB954" }}>
            <CheckCircle2 className="w-4 h-4" /> Completado
          </div>
        )}
        {status === "error" && (
          <div className="flex items-center gap-1.5 text-xs text-red-400">
            <XCircle className="w-4 h-4" /> Error
          </div>
        )}
        {status === "running" && (
          <div className="flex items-center gap-1.5 text-xs text-yellow-400">
            <RefreshCw className="w-4 h-4 animate-spin" /> Ejecutando...
          </div>
        )}
      </div>

      {/* CTA */}
      <div className="flex gap-3 mb-5">
        <Button
          onClick={handleRun}
          disabled={status === "running"}
          className="flex-1 h-11 gap-2 font-bold rounded-lg transition-all duration-200 active:scale-95"
          style={{
            background: status === "running" ? "rgba(29,185,84,0.3)" : "linear-gradient(135deg, #1DB954, #1ed760)",
            color: "#000",
            fontFamily: "DM Sans, sans-serif",
            opacity: status === "running" ? 0.7 : 1,
          }}
        >
          {status === "running" ? (
            <><RefreshCw className="w-4 h-4 animate-spin" /> Sincronizando...</>
          ) : (
            <><Play className="w-4 h-4" /> Sincronizar Ahora</>
          )}
        </Button>
        {(status === "success" || status === "error") && (
          <Button onClick={handleReset} variant="outline" className="border-white/10 text-white/60 hover:text-white hover:border-white/20">
            Limpiar
          </Button>
        )}
      </div>

      {/* Terminal logs */}
      {logs.length > 0 && (
        <div className="terminal-panel rounded-lg p-4 max-h-48 overflow-y-auto" style={{ minHeight: 60 }}>
          {logs.map((log, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 mb-1 text-xs leading-relaxed"
              style={{ color: LOG_COLORS[log.type], animation: "fadeInLine 0.15s ease-out" }}
            >
              <span className="flex-shrink-0 opacity-70 mt-0.5">{LOG_ICONS[log.type]}</span>
              <span className="font-mono">{log.text}</span>
            </div>
          ))}
          {status === "running" && (
            <div className="flex items-center gap-2 text-xs mt-1" style={{ color: "#1DB954" }}>
              <span className="inline-block w-2 h-4 rounded-sm" style={{ background: "#1DB954", animation: "blink 0.8s step-end infinite" }} />
            </div>
          )}
          <div ref={logsEndRef} />
        </div>
      )}

      {/* Resumen post-ETL */}
      {summary && <SummaryPanel summary={summary} />}

      <style>{`
        @keyframes fadeInLine {
          from { opacity: 0; transform: translateX(-4px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
