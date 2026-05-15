/**
 * SkeletonCard — Componentes de skeleton loader para el dashboard.
 *
 * Exports:
 *   Skeleton     — bloque simple con shimmer (tamaño vía `className`)
 *   SkeletonCard — tarjeta glass completa con 4 líneas dummy (para KPI cards)
 *   SkeletonList — lista de N filas con avatar circular + dos líneas de texto (default 5)
 *
 * El efecto `skeleton-shimmer` está definido en frontend/src/index.css.
 */

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn("rounded-md skeleton-shimmer", className)}
      style={{ background: "rgba(255,255,255,0.05)" }}
    />
  );
}

export function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div
      className={cn("glass-card rounded-xl p-5 space-y-3", className)}
    >
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-2/3" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-4/5" />
    </div>
  );
}

export function SkeletonList({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}
