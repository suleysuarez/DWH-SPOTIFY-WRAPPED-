/**
 * EmptyState — shown when the DWH has no data yet.
 */

import { Database, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";

interface EmptyStateProps {
  title?: string;
  description?: string;
  showEtlLink?: boolean;
}

export default function EmptyState({
  title = "Tu DWH está vacío",
  description = "Ve a la página ETL y sincroniza tus datos de Spotify.",
  showEtlLink = true,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
        style={{ background: "rgba(29, 185, 84, 0.1)", border: "1px solid rgba(29, 185, 84, 0.2)" }}
      >
        <Database className="w-7 h-7" style={{ color: "#1DB954" }} />
      </div>
      <h3 className="text-lg font-bold text-white mb-2" style={{ fontFamily: "Nunito, sans-serif" }}>
        {title}
      </h3>
      <p className="text-sm text-white/50 max-w-xs mb-6">{description}</p>
      {showEtlLink && (
        <Link href="/etl">
          <Button
            className="gap-2"
            style={{ background: "#1DB954", color: "#000", fontWeight: 700 }}
          >
            Ir a ETL
            <ArrowRight className="w-4 h-4" />
          </Button>
        </Link>
      )}
    </div>
  );
}
