import Navbar from "@/components/layout/Navbar";
import DwhStatusTable from "@/components/etl/DwhStatusTable";
import EtlHistoryTable from "@/components/etl/EtlHistoryTable";
import RunEtlPanel from "@/components/etl/RunEtlPanel";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import type { EtlStatusResponse } from "@/types/etl";
import { motion } from "framer-motion";

const EASE = [0.22, 1, 0.36, 1] as [number, number, number, number];
const fadeUp = (i: number) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: EASE, delay: 0.05 + i * 0.1 },
});

export default function Etl() {
  const { data, loading, error, refetch } = useApi<EtlStatusResponse>(endpoints.etl.status);

  const handleRunComplete = () => {
    setTimeout(() => refetch(), 1500);
  };

  return (
    <div style={{ minHeight: "100vh", background: "#121212", display: "flex", flexDirection: "column" }}>
      <Navbar />

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

        {/* ══ IZQUIERDA: contenido scrollable ══════════════════════════════════ */}
        <div style={{ flex: 1, overflowY: "auto", padding: "40px 48px", display: "flex", flexDirection: "column", gap: 24 }}>

          {/* Header */}
          <motion.div {...fadeUp(0)}>
            <h1 style={{ fontFamily: "DM Sans, sans-serif", fontSize: "clamp(1.8rem, 3vw, 2.6rem)", fontWeight: 900, color: "#fff", lineHeight: 1.1, marginBottom: 6 }}>
              Pipeline ETL
            </h1>
            <p style={{ fontSize: 14, color: "rgba(255,255,255,0.35)" }}>
              Monitorea y ejecuta los procesos de sincronización de tu Data Warehouse.
            </p>
          </motion.div>

          {/* Fila superior: RunEtlPanel + DwhStatusTable */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, alignItems: "start" }}>
            <motion.div {...fadeUp(1)}>
              <RunEtlPanel onRunComplete={handleRunComplete} />
            </motion.div>
            <motion.div {...fadeUp(2)}>
              <DwhStatusTable
                tables={data?.tables ?? null}
                loading={loading}
                error={error}
                onRetry={refetch}
              />
            </motion.div>
          </div>

          {/* Historial completo */}
          <motion.div {...fadeUp(3)}>
            <EtlHistoryTable />
          </motion.div>

        </div>

        {/* ══ DERECHA: video lateral fijo ══════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
          style={{
            flexShrink: 0,
            width: "calc((100vh - 57px) * (1080 / 1920))",
            position: "sticky",
            top: 0,
            height: "calc(100vh - 57px)",
            overflow: "hidden",
            background: "#121212",
          }}
        >
          {/* Gradient fusion left edge */}
          <div style={{ position: "absolute", inset: 0, zIndex: 2, background: "linear-gradient(to right, #121212 0%, transparent 22%)" }} />
          {/* Top/bottom fade */}
          <div style={{ position: "absolute", inset: 0, zIndex: 2, background: "linear-gradient(to bottom, rgba(18,18,18,0.5) 0%, transparent 10%, transparent 90%, rgba(18,18,18,0.5) 100%)" }} />
          <video
            src="/videos/etl.mp4"
            autoPlay
            muted
            loop
            playsInline
            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
          />
        </motion.div>

      </div>
    </div>
  );
}
