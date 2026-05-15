/**
 * EtlHistoryTable.tsx — Tabla paginada del historial completo de ejecuciones ETL.
 *
 * Gestiona su propia carga de datos (no recibe props de datos), llamando
 * directamente a GET /v1/etl/history con paginación y filtro por status.
 *
 * Comportamiento:
 *   - Carga inicialmente las primeras 5 ejecuciones (INITIAL_LIMIT).
 *   - "Ver más" carga PAGE_SIZE=10 adicionales y los añade a la lista.
 *   - "Ver menos" colapsa de vuelta a INITIAL_LIMIT.
 *   - El filtro de status (select) reinicia la lista al cambiar.
 *   - Cada fila es expandible para ver el detalle completo de la ejecución.
 *
 * Nota: usa fetch directo con getToken() en lugar de lib/api.ts, y tiene
 * hardcodeado `API_BASE = "http://127.0.0.1:8000"`.
 * La fecha se formatea con `es-CO` locale y timezone America/Bogota.
 */
import { useState, useEffect, useCallback, Fragment } from "react";
import { Skeleton } from "@/components/ui/SkeletonCard";
import { getToken } from "@/lib/auth";
import { CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, Filter, ChevronRight } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

interface EtlRun {
  id: number;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
  status: "success" | "error" | "running";
  error_message: string | null;
  artists_new: number;
  tracks_new: number;
  history_new: number;
  history_skipped: number;
}

const STATUS_LABELS: Record<string, string> = { success: "Exitosa", error: "Error", running: "En curso" };
const STATUS_COLORS: Record<string, string> = { success: "#1DB954", error: "#e74c3c", running: "#f39c12" };

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "rgba(255,255,255,0.4)";
  const Icon = status === "success" ? CheckCircle : status === "error" ? XCircle : Clock;
  return (
    <span
      className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full"
      style={{ background: `${color}22`, color }}
    >
      <Icon className="w-3 h-3" />
      {STATUS_LABELS[status] || status}
    </span>
  );
}

function formatDate(date: string | null) {
  if (!date) return "—";
  try {
    return new Date(date).toLocaleString("es-CO", {
      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "America/Bogota",
    });
  } catch { return "—"; }
}

interface TrackDetail {
  name: string;
  artist_name: string;
  album_name: string | null;
  album_image_url: string | null;
  duration_ms: number | null;
  popularity: number | null;
}

function DetailPanel({ run }: { run: EtlRun }) {
  const [showTracks, setShowTracks] = useState(false);
  const [tracks, setTracks] = useState<TrackDetail[]>([]);
  const [tracksLoading, setTracksLoading] = useState(false);

  const handleToggleTracks = async () => {
    if (showTracks) { setShowTracks(false); return; }
    if (tracks.length > 0) { setShowTracks(true); return; }
    setTracksLoading(true);
    setShowTracks(true);
    try {
      const token = getToken();
      const res = await fetch(`${API_BASE}/v1/etl/${run.id}/tracks`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTracks(data.tracks ?? []);
      }
    } catch {
      // silencioso — el panel simplemente muestra vacío
    } finally {
      setTracksLoading(false);
    }
  };

  return (
    <tr>
      <td colSpan={5} className="pb-3 pt-0">
        <div
          className="rounded-xl p-4 text-xs"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}
        >
          {/* ── Contadores ── */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
            <div>
              <p className="text-white/30 mb-1">Artistas nuevos</p>
              <p className="font-bold" style={{ color: run.artists_new > 0 ? "#1DB954" : "rgba(255,255,255,0.35)" }}>
                {run.artists_new > 0 ? `+${run.artists_new}` : "0"}
              </p>
            </div>
            <div>
              <p className="text-white/30 mb-1">Canciones nuevas</p>
              <div className="flex items-center gap-2">
                <p className="font-bold" style={{ color: run.tracks_new > 0 ? "#1DB954" : "rgba(255,255,255,0.35)" }}>
                  {run.tracks_new > 0 ? `+${run.tracks_new}` : "0"}
                </p>
                {run.tracks_new > 0 && (
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); handleToggleTracks(); }}
                    className="text-white/30 hover:text-white/60 transition-colors underline underline-offset-2"
                  >
                    {showTracks ? "ocultar" : "ver cuáles"}
                  </button>
                )}
              </div>
            </div>
            <div>
              <p className="text-white/30 mb-1">Historial nuevo</p>
              <p className="font-bold" style={{ color: run.history_new > 0 ? "#1DB954" : "rgba(255,255,255,0.35)" }}>
                {run.history_new > 0 ? `+${run.history_new}` : "0"}
              </p>
            </div>
            <div>
              <p className="text-white/30 mb-1">Omitidos</p>
              <p className="font-bold text-white/40">{run.history_skipped ?? 0}</p>
            </div>
          </div>

          {/* ── Lista de canciones insertadas ── */}
          {showTracks && (
            <div
              className="mb-3 rounded-lg p-3"
              style={{ background: "rgba(29,185,84,0.05)", border: "1px solid rgba(29,185,84,0.15)" }}
            >
              {tracksLoading ? (
                <p className="text-white/30 text-center py-2">Cargando canciones...</p>
              ) : tracks.length === 0 ? (
                <p className="text-white/30 text-center py-2">No se encontraron registros en el rango de esta ejecución.</p>
              ) : (
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {tracks.map((t, i) => (
                    <div key={i} className="flex items-center gap-2.5">
                      {t.album_image_url
                        ? <img src={t.album_image_url} alt={t.name} className="w-8 h-8 rounded flex-shrink-0 object-cover" />
                        : <div className="w-8 h-8 rounded flex-shrink-0 flex items-center justify-center text-sm" style={{ background: "rgba(29,185,84,0.1)", color: "#1DB954" }}>♪</div>}
                      <div className="min-w-0">
                        <p className="text-white/80 font-semibold truncate">{t.name}</p>
                        <p className="text-white/35 truncate">{t.artist_name}{t.album_name ? ` · ${t.album_name}` : ""}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {run.finished_at && (
            <p className="text-white/30 text-xs mb-2">
              Finalizado: <span className="text-white/50">{formatDate(run.finished_at)}</span>
            </p>
          )}

          {run.error_message && (
            <div
              className="mt-2 rounded-lg p-3"
              style={{ background: "rgba(231,76,60,0.08)", border: "1px solid rgba(231,76,60,0.2)" }}
            >
              <p className="text-xs font-semibold mb-1" style={{ color: "#e74c3c" }}>Error</p>
              <p className="font-mono text-xs break-all" style={{ color: "rgba(231,76,60,0.8)" }}>
                {run.error_message}
              </p>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}

export default function EtlHistoryTable() {
  const [runs, setRuns] = useState<EtlRun[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [expanded, setExpanded] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const INITIAL_LIMIT = 5;
  const PAGE_SIZE = 10;

  const fetchRuns = useCallback(async (offset: number, filter: string, append: boolean) => {
    try {
      const token = getToken();
      const params = new URLSearchParams({
        limit: String(append ? PAGE_SIZE : INITIAL_LIMIT),
        offset: String(offset),
      });
      if (filter) params.set("status", filter);
      const res = await fetch(`${API_BASE}/v1/etl/history?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setTotal(data.total ?? 0);
      if (append) {
        setRuns((prev) => [...prev, ...(data.runs ?? [])]);
      } else {
        setRuns(data.runs ?? []);
        setExpanded(false);
        setExpandedRows(new Set());
      }
    } catch {} finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchRuns(0, statusFilter, false);
  }, [statusFilter, fetchRuns]);

  const handleVerMas = async () => {
    if (!expanded) {
      setLoadingMore(true);
      setExpanded(true);
      await fetchRuns(INITIAL_LIMIT, statusFilter, true);
    } else {
      setRuns((prev) => prev.slice(0, INITIAL_LIMIT));
      setExpanded(false);
    }
  };

  const toggleRow = (id: number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const hasMore = !expanded && total > INITIAL_LIMIT;
  const showCollapse = expanded && runs.length > INITIAL_LIMIT;

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h3 className="text-sm font-bold text-white">Historial ETL</h3>
          <p className="text-xs text-white/40">{total} ejecuciones totales · haz clic en una fila para ver el detalle</p>
        </div>
        <div className="flex items-center gap-1">
          <Filter className="w-3 h-3 text-white/30" />
          <select
            aria-label="Filtrar por estado"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs rounded-lg px-2 py-1 border-0 outline-none cursor-pointer"
            style={{ background: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.7)" }}
          >
            <option value="">Todas</option>
            <option value="success">Exitosas</option>
            <option value="error">Con error</option>
            <option value="running">En curso</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
        </div>
      ) : runs.length === 0 ? (
        <p className="text-sm text-white/30 text-center py-6">No hay ejecuciones.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-white/30 border-b border-white/5">
                <th className="text-left pb-2 pr-3 font-medium">Inicio</th>
                <th className="text-left pb-2 pr-3 font-medium">Duración</th>
                <th className="text-left pb-2 pr-3 font-medium">Nuevos</th>
                <th className="text-left pb-2 font-medium">Estado</th>
                <th className="pb-2 w-5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {runs.map((run) => (
                <Fragment key={run.id}>
                  <tr
                    className="cursor-pointer transition-colors"
                    style={{ background: expandedRows.has(run.id) ? "rgba(29,185,84,0.04)" : undefined }}
                    onClick={() => toggleRow(run.id)}
                    onMouseEnter={(e) => { if (!expandedRows.has(run.id)) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = expandedRows.has(run.id) ? "rgba(29,185,84,0.04)" : ""; }}
                  >
                    <td className="py-2.5 pr-3 text-white/70">{formatDate(run.started_at)}</td>
                    <td className="py-2.5 pr-3 text-white/50">
                      {run.duration_seconds != null ? `${run.duration_seconds}s` : "—"}
                    </td>
                    <td className="py-2.5 pr-3">
                      {run.history_new > 0
                        ? <span style={{ color: "#1DB954" }}>+{run.history_new} canciones</span>
                        : <span className="text-white/30">Sin nuevos</span>}
                    </td>
                    <td className="py-2.5"><StatusBadge status={run.status} /></td>
                    <td className="py-2.5 text-right pr-1">
                      <ChevronRight
                        className="w-3.5 h-3.5 text-white/25 inline-block"
                        style={{
                          transform: expandedRows.has(run.id) ? "rotate(90deg)" : "none",
                          transition: "transform 0.15s ease",
                        }}
                      />
                    </td>
                  </tr>
                  {expandedRows.has(run.id) && <DetailPanel run={run} />}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && (hasMore || showCollapse) && (
        <button
          type="button"
          onClick={handleVerMas}
          disabled={loadingMore}
          className="mt-3 w-full flex items-center justify-center gap-1 text-xs py-2 rounded-lg"
          style={{ background: "rgba(29,185,84,0.08)", color: "#1DB954", border: "1px solid rgba(29,185,84,0.2)" }}
        >
          {loadingMore ? "Cargando..." : showCollapse
            ? <><ChevronUp className="w-3 h-3" /> Ver menos</>
            : <><ChevronDown className="w-3 h-3" /> Ver más ({total - INITIAL_LIMIT} restantes)</>}
        </button>
      )}
    </div>
  );
}
