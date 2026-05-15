/**
 * usePersistFn — Referencia estable a una función sin declarar dependencias.
 *
 * La función retornada nunca cambia de referencia entre renders (útil para
 * listeners y callbacks que no deben invalidar efectos), pero siempre ejecuta
 * la última versión de `fn` capturada a través de un ref interno.
 * Alternativa a useCallback cuando el array de dependencias sería tedioso.
 */

import { useRef } from "react";

type noop = (...args: any[]) => any;
export function usePersistFn<T extends noop>(fn: T) {
  const fnRef = useRef<T>(fn);
  fnRef.current = fn;

  const persistFn = useRef<T>(null);
  if (!persistFn.current) {
    persistFn.current = function (this: unknown, ...args) {
      return fnRef.current!.apply(this, args);
    } as T;
  }

  return persistFn.current!;
}
