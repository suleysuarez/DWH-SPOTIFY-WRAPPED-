/**
 * utils.ts — Utilidad de fusión de clases CSS.
 * `cn` combina clsx y tailwind-merge para resolver conflictos de clases Tailwind.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
