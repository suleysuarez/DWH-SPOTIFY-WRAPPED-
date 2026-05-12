export type TableStatus = "loaded" | "empty" | "stale";

export interface DwhTable {
  table_name: string;
  record_count: number;
  last_sync: string | null;
  status: TableStatus;
}

export interface EtlRun {
  id: string;
  started_at: string;
  finished_at: string | null;
  status: "success" | "error" | "running";
  duration_seconds: number | null;
  records_extracted: number;
  records_loaded: number;
  error_message?: string;
}

export interface EtlStatusResponse {
  tables: DwhTable[];
  recent_runs: EtlRun[];
}

export interface EtlRunResponse {
  run_id: string;
  status: "started" | "running" | "success" | "error";
  logs: string[];
  message?: string;
}

export interface EtlLogLine {
  type: "success" | "error" | "info" | "warning";
  text: string;
  timestamp?: string;
}
