/**
 * RunEtlPanel.tsx — Panel para disparar el pipeline ETL con salida tipo terminal.
 *
 * Props:
 *   onRunComplete → () => void  (callback que llama Etl.tsx para refrescar status)
 *
 * Estados internos (RunStatus): "idle" | "running" | "success" | "error"
 *
 * Flujo al hacer clic en "Sincronizar Ahora":
 * 1. Muestra log inicial "Iniciando proceso ETL...".
 * 2. Llama a POST /v1/etl/run vía endpoints.etl.run().
 * 3. Anima los logs de la respuesta uno a uno (delay 120ms entre cada uno).
 * 4. Muestra toast (sonner) de éxito o error.
 * 5. Llama a onRunComplete() para que Etl.tsx refresque DwhStatusTable.
 *
 * parseLogLine() clasifica cada string del backend como "success" | "error" |
 * "warning" | "info" según palabras clave (heurística simple).
 * El cursor parpadeante indica que el ETL sigue ejecutándose.
 */

import { useState, useRef, useEffect } from "react";
import { endpoints, ApiError } from "@/lib/api";
import type { EtlLogLine } from "@/types/etl";
import { Button } from "@/components/ui/button";
import { Play, RefreshCw, CheckCircle2, XCircle, Terminal, Info, AlertCircle } from "lucide-react";
import { toast } from "sonner";

interface RunEtlPanelProps {
  onRunComplete?: () => void;
}

type RunStatus = "idle" | "running" | "success" | "error";

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

export default function RunEtlPanel({ onRunComplete }: RunEtlPanelProps) {
  const [status, setStatus] = useState<RunStatus>("idle");
  const [logs, setLogs] = useState<EtlLogLine[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleRun = async () => {
    setStatus("running");
    setLogs([]);

    // Simulate progressive log display while waiting for API
    const progressLogs: EtlLogLine[] = [
      { type: "info", text: "Iniciando proceso ETL..." },
    ];
    setLogs([...progressLogs]);

    try {
      const result = await endpoints.etl.run();

      // Parse and display logs from response
      const parsedLogs: EtlLogLine[] = (result.logs ?? []).map(parseLogLine);

      // Animate logs one by one
      for (let i = 0; i < parsedLogs.length; i++) {
        await new Promise((r) => setTimeout(r, 120));
        setLogs((prev) => [...prev, parsedLogs[i]]);
      }

      if (result.status === "success" || result.status === "started") {
        setLogs((prev) => [
          ...prev,
          { type: "success", text: "ETL completado exitosamente." },
        ]);
        setStatus("success");
        toast.success("ETL completado", { description: "Datos sincronizados correctamente." });
        onRunComplete?.();
      } else {
        setLogs((prev) => [
          ...prev,
          { type: "error", text: `${result.message ?? "ETL finalizó con errores."}` },
        ]);
        setStatus("error");
        toast.error("ETL falló", { description: result.message });
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Error inesperado al ejecutar ETL.";
      setLogs((prev) => [
        ...prev,
        { type: "error", text: `${message}` },
      ]);
      setStatus("error");
      toast.error("Error ETL", { description: message });
    }
  };

  const handleReset = () => {
    setStatus("idle");
    setLogs([]);
  };

  return (
    <div className="glass-card rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "rgba(29, 185, 84, 0.15)" }}
          >
            <Terminal className="w-4 h-4" style={{ color: "#1DB954" }} />
          </div>
          <div>
            <h3
              className="text-sm font-bold text-white"
              style={{ fontFamily: "DM Sans, sans-serif" }}
            >
              Ejecutar ETL
            </h3>
            <p className="text-xs text-white/40">Sincronizar datos de Spotify</p>
          </div>
        </div>

        {/* Status indicator */}
        {status === "success" && (
          <div className="flex items-center gap-1.5 text-xs" style={{ color: "#1DB954" }}>
            <CheckCircle2 className="w-4 h-4" />
            Completado
          </div>
        )}
        {status === "error" && (
          <div className="flex items-center gap-1.5 text-xs text-red-400">
            <XCircle className="w-4 h-4" />
            Error
          </div>
        )}
        {status === "running" && (
          <div className="flex items-center gap-1.5 text-xs text-yellow-400">
            <RefreshCw className="w-4 h-4 animate-spin" />
            Ejecutando...
          </div>
        )}
      </div>

      {/* CTA Button */}
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
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Sincronizando...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Sincronizar Ahora
            </>
          )}
        </Button>

        {(status === "success" || status === "error") && (
          <Button
            onClick={handleReset}
            variant="outline"
            className="border-white/10 text-white/60 hover:text-white hover:border-white/20"
          >
            Limpiar
          </Button>
        )}
      </div>

      {/* Terminal log panel */}
      {logs.length > 0 && (
        <div
          className="terminal-panel rounded-lg p-4 max-h-64 overflow-y-auto"
          style={{ minHeight: 80 }}
        >
          {logs.map((log, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 mb-1 text-xs leading-relaxed"
              style={{
                color: LOG_COLORS[log.type],
                animation: "fadeInLine 0.15s ease-out",
              }}
            >
              <span className="flex-shrink-0 opacity-70 mt-0.5">
                {LOG_ICONS[log.type]}
              </span>
              <span className="font-mono">{log.text}</span>
            </div>
          ))}
          {status === "running" && (
            <div className="flex items-center gap-2 text-xs mt-1" style={{ color: "#1DB954" }}>
              <span
                className="inline-block w-2 h-4 rounded-sm"
                style={{
                  background: "#1DB954",
                  animation: "blink 0.8s step-end infinite",
                }}
              />
            </div>
          )}
          <div ref={logsEndRef} />
        </div>
      )}

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
