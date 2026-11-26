/** El backend guarda y entrega las horas en UTC; aquí se pasan a la hora local del navegador. */

/** Convierte una hora UTC (0-23) a la hora local. */
export function toLocalHour(hourUtc: number): number {
  const offsetHours = Math.floor(new Date().getTimezoneOffset() / 60);
  return (hourUtc - offsetHours + 24) % 24;
}

/** 7 → "07:00" */
export function formatHour(hour: number): string {
  return `${String(hour).padStart(2, "0")}:00`;
}
