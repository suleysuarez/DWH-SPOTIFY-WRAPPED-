/**
 * ETL Page — monitor and execute ETL processes.
 * Sections: DWH Status, ETL History, Run ETL
 * API: GET /v1/etl/status, POST /v1/etl/run
 */

import AppLayout from "@/components/layout/AppLayout";
import DwhStatusTable from "@/components/etl/DwhStatusTable";
import EtlHistoryTable from "@/components/etl/EtlHistoryTable";
import RunEtlPanel from "@/components/etl/RunEtlPanel";
import { useApi } from "@/hooks/useApi";
import { endpoints } from "@/lib/api";
import type { EtlStatusResponse } from "@/types/etl";

export default function Etl() {
  const { data, loading, error, refetch } = useApi<EtlStatusResponse>(endpoints.etl.status);

  const handleRunComplete = () => {
    // Refresh status after ETL run
    setTimeout(() => refetch(), 1500);
  };

  return (
    <AppLayout>
      {/* Header */}
      <div className="mb-8">
        <h1
          className="text-3xl font-black text-white mb-1"
          style={{ fontFamily: "Nunito, sans-serif" }}
        >
          ETL
        </h1>
        <p className="text-sm text-white/40">
          Monitorea y ejecuta los procesos de sincronización de tu Data Warehouse.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: DWH Status + History */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Section A: DWH Status */}
          <DwhStatusTable
            tables={data?.tables ?? null}
            loading={loading}
            error={error}
            onRetry={refetch}
          />

          {/* Section B: ETL History */}
          <EtlHistoryTable
            runs={data?.recent_runs ?? null}
            loading={loading}
          />
        </div>

        {/* Right column: Run ETL */}
        <div className="lg:col-span-1">
          <RunEtlPanel onRunComplete={handleRunComplete} />
        </div>
      </div>
    </AppLayout>
  );
}
