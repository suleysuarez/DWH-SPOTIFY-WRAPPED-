import { useState, useEffect, useCallback } from "react";
import { Skeleton } from "@/components/ui/SkeletonCard";
import { getToken } from "@/lib/auth";
import { CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, Filter } from "lucide-react";
const API_BASE = "http://127.0.0.1:8000";
interface EtlRun { id: number; started_at: string; finished_at: string | null; duration_seconds: number | null; status: "success" | "error" | "running"; error_message: string | null; artists_new: number; tracks_new: number; history_new: number; history_skipped: number; }
const STATUS_LABELS: Record<string, string> = { success: "Exitosa", error: "Error", running: "En curso" };
const STATUS_COLORS: Record<string, string> = { success: "#1DB954", error: "#e74c3c", running: "#f39c12" };
function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "rgba(255,255,255,0.4)";
  const Icon = status === "success" ? CheckCircle : status === "error" ? XCircle : Clock;
  return <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: `${color}22`, color }}><Icon className="w-3 h-3" />{STATUS_LABELS[status] || status}</span>;
}
function formatDate(date: string | null) {
  if (!date) return "—";
  try { return new Date(date).toLocaleString("es-CO", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "America/Bogota" }); } catch { return "—"; }
}
export default function EtlHistoryTable() {
  const [runs, setRuns] = useState<EtlRun[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [expanded, setExpanded] = useState(false);
  const INITIAL_LIMIT = 5; const PAGE_SIZE = 10;
  const fetchRuns = useCallback(async (offset: number, filter: string, append: boolean) => {
    try {
      const token = getToken();
      const params = new URLSearchParams({ limit: String(append ? PAGE_SIZE : INITIAL_LIMIT), offset: String(offset) });
      if (filter) params.set("status", filter);
      const res = await fetch(`${API_BASE}/v1/etl/history?${params}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) return;
      const data = await res.json();
      setTotal(data.total ?? 0);
      if (append) { setRuns((prev) => [...prev, ...(data.runs ?? [])]); } else { setRuns(data.runs ?? []); setExpanded(false); }
    } catch {} finally { setLoading(false); setLoadingMore(false); }
  }, []);
  useEffect(() => { setLoading(true); fetchRuns(0, statusFilter, false); }, [statusFilter, fetchRuns]);
  const handleVerMas = async () => {
    if (!expanded) { setLoadingMore(true); setExpanded(true); await fetchRuns(INITIAL_LIMIT, statusFilter, true); }
    else { setRuns((prev) => prev.slice(0, INITIAL_LIMIT)); setExpanded(false); }
  };
  const hasMore = !expanded && total > INITIAL_LIMIT;
  const showCollapse = expanded && runs.length > INITIAL_LIMIT;
  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div><h3 className="text-sm font-bold text-white">Historial ETL</h3><p className="text-xs text-white/40">{total} ejecuciones totales</p></div>
        <div className="flex items-center gap-1"><Filter className="w-3 h-3 text-white/30" />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="text-xs rounded-lg px-2 py-1 border-0 outline-none cursor-pointer" style={{ background: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.7)" }}>
            <option value="">Todas</option><option value="success">Exitosas</option><option value="error">Con error</option><option value="running">En curso</option>
          </select></div>
      </div>
      {loading ? <div className="space-y-2">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
       : runs.length === 0 ? <p className="text-sm text-white/30 text-center py-6">No hay ejecuciones.</p>
       : <div className="overflow-x-auto"><table className="w-full text-xs">
           <thead><tr className="text-white/30 border-b border-white/5"><th className="text-left pb-2 pr-3 font-medium">Inicio</th><th className="text-left pb-2 pr-3 font-medium">Duración</th><th className="text-left pb-2 pr-3 font-medium">Nuevos</th><th className="text-left pb-2 font-medium">Estado</th></tr></thead>
           <tbody className="divide-y divide-white/5">{runs.map((run) => (<tr key={run.id}><td className="py-2 pr-3 text-white/70">{formatDate(run.started_at)}</td><td className="py-2 pr-3 text-white/50">{run.duration_seconds != null ? `${run.duration_seconds}s` : "—"}</td><td className="py-2 pr-3">{run.history_new > 0 ? <span style={{ color: "#1DB954" }}>+{run.history_new} canciones</span> : <span className="text-white/30">Sin nuevos</span>}</td><td className="py-2"><StatusBadge status={run.status} /></td></tr>))}</tbody>
         </table></div>}
      {!loading && (hasMore || showCollapse) && (<button onClick={handleVerMas} disabled={loadingMore} className="mt-3 w-full flex items-center justify-center gap-1 text-xs py-2 rounded-lg" style={{ background: "rgba(29,185,84,0.08)", color: "#1DB954", border: "1px solid rgba(29,185,84,0.2)" }}>{loadingMore ? "Cargando..." : showCollapse ? <><ChevronUp className="w-3 h-3" /> Ver menos</> : <><ChevronDown className="w-3 h-3" /> Ver más ({total - INITIAL_LIMIT} restantes)</>}</button>)}
    </div>
  );
}
