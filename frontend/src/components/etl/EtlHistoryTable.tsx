/**
 * EtlHistoryTable – shows recent ETL runs with duration, status, and metrics.
 */

import type { EtlRun } from "@/types/etl";
import { Skeleton } from "@/components/ui/SkeletonCard";
import { History, CheckCircle2, XCircle, Loader2 } from "lucide-react";

interface EtlHistoryTableProps {
  runs: EtlRun[] | null;
  loading: boolean;
}

function RunStatusIcon({ status }: { status: EtlRun["status"] }) {
  if (status === "success") return <CheckCircle2 className="w-4 h-4" style={{ color: "#1DB954" }} />;
  if (status === "error") return <XCircle className="w-4 h-4 text-red-400" />;
  return <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />;
}

export default function EtlHistoryTable({ runs, loading }: EtlHistoryTableProps) {
  const formatDate = (date: string | null) => {
    if (!date) return "—";
    try {
      return new Date(date).toLocaleString("es-CO", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "America/Bogota",
      });
    } catch {
      return "—";
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return "—";
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center gap-2 mb-5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "rgba(29, 185, 84, 0.15)" }}
        >
          <History className="w-4 h-4" style={{ color: "#1DB954" }} />
        </div>
        <div>
          <h3
            className="text-sm font-bold text-white"
            style={{ fontFamily: "Nunito, sans-serif" }}
          >
            Historial ETL
          </h3>
          <p className="text-xs text-white/40">Ejecuciones recientes</p>
        </div>
      </div>

      {loading && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="w-4 h-4 rounded-full flex-shrink-0" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      )}

      {!loading && (!runs || runs.length === 0) && (
        <p className="text-sm text-white/30 py-4">No hay ejecuciones registradas.</p>
      )}

      {!loading && runs && runs.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                <th className="text-left text-xs text-white/40 font-medium pb-3 pr-4 w-8"></th>
                <th className="text-left text-xs text-white/40 font-medium pb-3 pr-4">Inicio</th>
                <th className="text-right text-xs text-white/40 font-medium pb-3 px-4">Duración</th>
                <th className="text-right text-xs text-white/40 font-medium pb-3 px-4">Extraídos</th>
                <th className="text-right text-xs text-white/40 font-medium pb-3 pl-4">Cargados</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="border-b transition-colors"
                  style={{ borderColor: "rgba(255,255,255,0.04)" }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLTableRowElement).style.background = "rgba(255,255,255,0.02)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLTableRowElement).style.background = "transparent";
                  }}
                >
                  <td className="py-3 pr-4">
                    <RunStatusIcon status={run.status} />
                  </td>
                  <td className="py-3 pr-4 text-xs text-white/60">{formatDate(run.started_at)}</td>
                  <td className="py-3 px-4 text-right text-xs font-mono text-white/50">
                    {formatDuration(run.duration_seconds)}
                  </td>
                  <td className="py-3 px-4 text-right text-xs text-white/60">
                    {run.records_extracted.toLocaleString()}
                  </td>
                  <td className="py-3 pl-4 text-right text-xs font-bold" style={{ color: "#1DB954" }}>
                    {run.records_loaded.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}