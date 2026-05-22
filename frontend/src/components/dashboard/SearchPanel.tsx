import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Music2, Mic2, Star, Users, Play, ExternalLink } from "lucide-react";
import { getToken } from "@/lib/auth";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

type SearchType = "all" | "artist" | "track";

interface ArtistResult {
  artist_id: number;
  name: string;
  image_url: string | null;
  genres: string[];
  popularity: number | null;
  followers_count: number | null;
  play_count: number;
}

interface TrackResult {
  track_id: number;
  name: string;
  album_name: string | null;
  album_image_url: string | null;
  duration_ms: number | null;
  popularity: number | null;
  artist_name: string;
  play_count: number;
}

type Selected = { kind: "artist"; data: ArtistResult } | { kind: "track"; data: TrackResult };

function formatDuration(ms: number | null) {
  if (!ms) return "—";
  const m = Math.floor(ms / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatFollowers(n: number | null) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return String(n);
}

// ── Chip de stat ─────────────────────────────────────────────────────────────
function Chip({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4, padding: "14px 18px", borderRadius: 14, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)", minWidth: 100 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 5, color }}>
        {icon}
        <span style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", letterSpacing: "0.06em", textTransform: "uppercase" }}>{label}</span>
      </div>
      <p style={{ fontFamily: "DM Sans, sans-serif", fontSize: 20, fontWeight: 900, color: "#fff", lineHeight: 1 }}>{value}</p>
    </div>
  );
}

// ── Tarjeta de resultado en la lista ─────────────────────────────────────────
function ResultCard({ item, kind, selected, onClick }: {
  item: ArtistResult | TrackResult;
  kind: "artist" | "track";
  selected: boolean;
  onClick: () => void;
}) {
  const image = kind === "artist" ? (item as ArtistResult).image_url : (item as TrackResult).album_image_url;
  const sub   = kind === "artist"
    ? ((item as ArtistResult).genres.slice(0, 1)[0] || "Artista")
    : (item as TrackResult).artist_name;

  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ y: -3 }}
      whileTap={{ scale: 0.97 }}
      style={{
        display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
        padding: "12px 10px", borderRadius: 14, cursor: "pointer", minWidth: 90, maxWidth: 110,
        background: selected ? "rgba(29,185,84,0.12)" : "rgba(255,255,255,0.04)",
        border: selected ? "1px solid rgba(29,185,84,0.4)" : "1px solid rgba(255,255,255,0.07)",
        transition: "background 0.15s, border 0.15s",
      }}
    >
      {image
        ? <img src={image} alt={item.name} style={{ width: 60, height: 60, borderRadius: kind === "artist" ? "50%" : 10, objectFit: "cover", flexShrink: 0 }} />
        : <div style={{ width: 60, height: 60, borderRadius: kind === "artist" ? "50%" : 10, background: "rgba(29,185,84,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, flexShrink: 0 }}>
            {kind === "artist" ? "🎤" : "♪"}
          </div>
      }
      <div style={{ width: "100%", textAlign: "center" }}>
        <p style={{ fontSize: 11, fontWeight: 700, color: selected ? "#fff" : "rgba(255,255,255,0.8)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.name}</p>
        <p style={{ fontSize: 10, color: "rgba(255,255,255,0.35)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginTop: 2 }}>{sub}</p>
      </div>
      <span style={{ fontSize: 10, fontWeight: 700, color: "#1DB954" }}>{item.play_count} plays</span>
    </motion.button>
  );
}

// ── Panel de detalle ─────────────────────────────────────────────────────────
function DetailPanel({ item }: { item: Selected }) {
  const isArtist = item.kind === "artist";
  const a = isArtist ? item.data as ArtistResult : null;
  const t = !isArtist ? item.data as TrackResult : null;

  const image      = isArtist ? a!.image_url      : t!.album_image_url;
  const title      = isArtist ? a!.name           : t!.name;
  const subtitle   = isArtist ? (a!.genres.slice(0, 2).join(" · ") || "Artista") : t!.artist_name;
  const playCount  = isArtist ? a!.play_count     : t!.play_count;
  const popularity = isArtist ? a!.popularity     : t!.popularity;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      style={{
        display: "flex", gap: 28, alignItems: "flex-start",
        padding: "24px", borderRadius: 20,
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.08)",
        marginTop: 24,
      }}
    >
      {/* Imagen cuadrada */}
      <div style={{ flexShrink: 0, width: 180, height: 180, borderRadius: isArtist ? "50%" : 16, overflow: "hidden", boxShadow: "0 8px 40px rgba(0,0,0,0.5)" }}>
        {image
          ? <img src={image} alt={title} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
          : <div style={{ width: "100%", height: "100%", background: "rgba(29,185,84,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 56 }}>
              {isArtist ? "🎤" : "🎵"}
            </div>
        }
      </div>

      {/* Info */}
      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Título */}
        <div>
          <p style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
            {isArtist ? "Artista" : "Canción"}
          </p>
          <h3 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(1.4rem,2.5vw,2.2rem)", fontWeight: 900, color: "#fff", lineHeight: 1.1, marginBottom: 4 }}>{title}</h3>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.5)" }}>{subtitle}</p>
        </div>

        {/* Stats chips */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <Chip icon={<Play size={13} />}  label="Reproducciones" value={String(playCount)} color="#1DB954" />
          <Chip icon={<Star size={13} />}  label="Popularidad"    value={popularity != null ? `${popularity}/100` : "—"} color="#a78bfa" />
          {isArtist && (
            <Chip icon={<Users size={13} />} label="Seguidores" value={formatFollowers(a!.followers_count)} color="#4f8ef7" />
          )}
          {!isArtist && (
            <Chip icon={<Music2 size={13} />} label="Duración" value={formatDuration(t!.duration_ms)} color="#4f8ef7" />
          )}
        </div>

        {/* Géneros (solo artista) */}
        {isArtist && a!.genres.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {a!.genres.slice(0, 6).map((g, i) => (
              <span key={i} style={{ fontSize: 11, padding: "4px 12px", borderRadius: 20, background: "rgba(167,139,250,0.1)", color: "#a78bfa", border: "1px solid rgba(167,139,250,0.2)" }}>{g}</span>
            ))}
          </div>
        )}

        {/* Álbum (solo canción) */}
        {!isArtist && t!.album_name && (
          <p style={{ fontSize: 13, color: "rgba(255,255,255,0.3)" }}>
            Álbum: <span style={{ color: "rgba(255,255,255,0.6)" }}>{t!.album_name}</span>
          </p>
        )}

        {/* Botón abrir en Spotify */}
        <a
          href={`https://open.spotify.com/${isArtist ? "artist" : "track"}/${isArtist ? a!.spotify_id : t!.spotify_id}`}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            padding: "10px 20px", borderRadius: 24,
            background: "#1DB954", color: "#000",
            fontFamily: "DM Sans, sans-serif", fontWeight: 700, fontSize: 14,
            textDecoration: "none", width: "fit-content",
            transition: "opacity 0.15s",
          }}
          onMouseEnter={e => (e.currentTarget.style.opacity = "0.85")}
          onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
        >
          <ExternalLink size={15} />
          Abrir en Spotify
        </a>
      </div>
    </motion.div>
  );
}

// ── Componente principal ─────────────────────────────────────────────────────
export default function SearchPanel() {
  const [q, setQ]           = useState("");
  const [type, setType]     = useState<SearchType>("all");
  const [artists, setArtists] = useState<ArtistResult[]>([]);
  const [tracks, setTracks]   = useState<TrackResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [selected, setSelected] = useState<Selected | null>(null);
  const inputRef  = useRef<HTMLInputElement>(null);
  const debounce  = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!q.trim()) { setArtists([]); setTracks([]); setSelected(null); setSearched(false); return; }
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = setTimeout(async () => {
      setLoading(true);
      try {
        const token = getToken();
        const params = new URLSearchParams({ q: q.trim(), type, limit: "10" });
        const res = await fetch(`${API_BASE}/v1/search?${params}`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) return;
        const data = await res.json();
        setArtists(data.artists ?? []);
        setTracks(data.tracks ?? []);
        setSearched(true);
        setSelected(null);
      } catch {
      } finally { setLoading(false); }
    }, 350);
  }, [q, type]);

  const total = artists.length + tracks.length;

  const TYPE_TABS: { key: SearchType; label: string }[] = [
    { key: "all",    label: "Todo"      },
    { key: "artist", label: "Artistas"  },
    { key: "track",  label: "Canciones" },
  ];

  return (
    <div>
      {/* ── Barra de búsqueda ── */}
      <div style={{
        display: "flex", alignItems: "center", gap: 12,
        background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 16, padding: "14px 20px", marginBottom: 16,
      }}>
        <Search size={20} style={{ color: "#1DB954", flexShrink: 0 }} />
        <input
          ref={inputRef}
          type="text"
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Busca un artista o canción de tu historial..."
          style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: "#fff", fontSize: 16, fontFamily: "DM Sans, sans-serif" }}
        />
        {loading && <span style={{ fontSize: 12, color: "rgba(255,255,255,0.3)" }}>Buscando...</span>}
        {q && !loading && (
          <button type="button" onClick={() => { setQ(""); inputRef.current?.focus(); }}
            style={{ background: "none", border: "none", cursor: "pointer", color: "rgba(255,255,255,0.3)", padding: 0, display: "flex" }}>
            <X size={18} />
          </button>
        )}
      </div>

      {/* ── Filtros de tipo ── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {TYPE_TABS.map(t => (
          <button key={t.key} type="button" onClick={() => setType(t.key)}
            style={{
              padding: "6px 18px", borderRadius: 20, fontSize: 13, fontWeight: 700, cursor: "pointer",
              fontFamily: "DM Sans, sans-serif",
              background: type === t.key ? "rgba(29,185,84,0.18)" : "rgba(255,255,255,0.05)",
              color:      type === t.key ? "#1DB954" : "rgba(255,255,255,0.4)",
              border:     type === t.key ? "1px solid rgba(29,185,84,0.35)" : "1px solid transparent",
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Sin búsqueda ── */}
      {!q && (
        <p style={{ fontSize: 14, color: "rgba(255,255,255,0.2)", textAlign: "center", padding: "32px 0" }}>
          Escribe para buscar dentro de tu historial de reproducción
        </p>
      )}

      {/* ── Sin resultados ── */}
      {q && searched && total === 0 && !loading && (
        <p style={{ fontSize: 14, color: "rgba(255,255,255,0.25)", textAlign: "center", padding: "32px 0" }}>
          Sin resultados para "{q}"
        </p>
      )}

      {/* ── Resultados ── */}
      {total > 0 && (
        <div>
          {artists.length > 0 && (
            <div style={{ marginBottom: tracks.length > 0 ? 20 : 0 }}>
              {type === "all" && (
                <p style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", letterSpacing: "0.08em", marginBottom: 10 }}>ARTISTAS</p>
              )}
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {artists.map(a => (
                  <ResultCard
                    key={`a-${a.artist_id}`}
                    item={a} kind="artist"
                    selected={selected?.kind === "artist" && selected.data.artist_id === a.artist_id}
                    onClick={() => setSelected({ kind: "artist", data: a })}
                  />
                ))}
              </div>
            </div>
          )}

          {tracks.length > 0 && (
            <div>
              {type === "all" && (
                <p style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", letterSpacing: "0.08em", marginBottom: 10 }}>CANCIONES</p>
              )}
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {tracks.map(t => (
                  <ResultCard
                    key={`t-${t.track_id}`}
                    item={t} kind="track"
                    selected={selected?.kind === "track" && selected.data.track_id === t.track_id}
                    onClick={() => setSelected({ kind: "track", data: t })}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Detalle ── */}
      <AnimatePresence>
        {selected && <DetailPanel key={selected.kind === "artist" ? `a${selected.data.artist_id}` : `t${selected.data.track_id}`} item={selected} />}
      </AnimatePresence>
    </div>
  );
}
