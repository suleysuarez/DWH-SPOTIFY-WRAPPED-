/**
 * DwhStatusTable.tsx — Tabla de estado de las tablas del DWH.
 *
 * Muestra para cada tabla: nombre, número de registros, última sync y badge de estado.
 * Los datos provienen de GET /v1/etl/status (campo `tables`).
 *
 * Props:
 *   tables  → DwhTable[] | null
 *   loading → boolean
 *   error   → string | null
 *   onRetry → () => void
 *
 * Badges de estado (statusConfig):
 *   "loaded" → verde (#1DB954)   — tabla tiene datos.
 *   "empty"  → blanco/40         — tabla vacía.
 *   "stale"  → naranja (#FFA500) — no implementado actualmente en el backend.
 *
 * La fecha de última sync se formatea con `es-UY` locale (dd MMM HH:mm).
 */

import type { DwhTable, TableStatus } from "@/types/etl";
import { Skeleton } from "@/components/ui/SkeletonCard";
import ErrorState from "@/components/ui/ErrorState";
import { Database } from "lucide-react";

interface DwhStatusTableProps {
  tables: DwhTable[] | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

const statusConfig: Record<TableStatus, { label: string; bg: string; color: string }> = {
  loaded: { label: "Cargado", bg: "rgba(29,185,84,0.12)", color: "#1DB954" },
  empty: { label: "Vacío", bg: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.4)" },
  stale: { label: "Desactualizado", bg: "rgba(255,165,0,0.12)", color: "#FFA500" },
};

function StatusBadge({ status }: { status: TableStatus }) {
  const cfg = statusConfig[status] ?? statusConfig.empty;
  return (
    <span
      className="text-xs font-semibold px-2.5 py-1 rounded-full"
      style={{ background: cfg.bg, color: cfg.color }}
    >
      {cfg.label}
    </span>
  );
}

export default function DwhStatusTable({ tables, loading, error, onRetry }: DwhStatusTableProps) {
  const formatDate = (date: string | null) => {
    if (!date) return "—";
    try {
      return new Date(date).toLocaleString("es-UY", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "—";
    }
  };

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center gap-2 mb-5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: "rgba(29, 185, 84, 0.15)" }}
        >
          <Database className="w-4 h-4" style={{ color: "#1DB954" }} />
        </div>
        <div>
          <h3
            className="text-sm font-bold text-white"
            style={{ fontFamily: "DM Sans, sans-serif" }}
          >
            Estado del DWH
          </h3>
          <p className="text-xs text-white/40">Tablas y registros actuales</p>
        </div>
      </div>

      {loading && (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
          ))}
        </div>
      )}

      {!loading && error && <ErrorState message={error} onRetry={onRetry} />}

      {!loading && !error && (!tables || tables.length === 0) && (
        <p className="text-sm text-white/30 py-4">No se encontraron tablas en el DWH.</p>
      )}

      {!loading && !error && tables && tables.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                <th className="text-left text-xs text-white/40 font-medium pb-3 pr-4">Tabla</th>
                <th className="text-right text-xs text-white/40 font-medium pb-3 px-4">Registros</th>
                <th className="text-left text-xs text-white/40 font-medium pb-3 px-4">Última Sync</th>
                <th className="text-left text-xs text-white/40 font-medium pb-3 pl-4">Estado</th>
              </tr>
            </thead>
            <tbody>
              {tables.map((table) => (
                <tr
                  key={table.table_name}
                  className="border-b transition-colors"
                  style={{
                    borderColor: "rgba(255,255,255,0.04)",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLTableRowElement).style.background = "rgba(255,255,255,0.02)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLTableRowElement).style.background = "transparent";
                  }}
                >
                  <td className="py-3 pr-4">
                    <span className="font-mono text-xs text-white/70">{table.table_name}</span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="font-bold text-white">{table.record_count.toLocaleString()}</span>
                  </td>
                  <td className="py-3 px-4 text-xs text-white/40">{formatDate(table.last_sync)}</td>
                  <td className="py-3 pl-4">
                    <StatusBadge status={table.status} />
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
