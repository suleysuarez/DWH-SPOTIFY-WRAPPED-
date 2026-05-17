/**
 * ErrorState — Estado de error para fallos en llamadas a la API.
 *
 * Props:
 *   message → string    (default: "Error al cargar los datos.")
 *   onRetry → () => void (opcional) — muestra botón "Reintentar" si se pasa
 *
 * Usado en todos los componentes del dashboard y ETL como fallback de error.
 */

import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message = "Error al cargar los datos.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div
        className="w-14 h-14 rounded-full flex items-center justify-center mb-4"
        style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)" }}
      >
        <AlertCircle className="w-6 h-6 text-red-400" />
      </div>
      <p className="text-sm text-white/60 mb-4 max-w-xs">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="gap-2 border-white/10 text-white/70 hover:text-white hover:border-white/20"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reintentar
        </Button>
      )}
    </div>
  );
}
