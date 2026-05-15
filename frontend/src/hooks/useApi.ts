/**
 * useApi — Hook genérico de fetching con estados loading/error/data/refetch.
 *
 * El `fetcher` se ejecuta en el montaje y en cada llamada a `refetch()`.
 * Los errores ApiError y Error se exponen como strings en el estado `error`.
 * No cancela requests — si el componente se desmonta antes de que resuelva, el
 * estado se actualizará igualmente (sin causar errores, pero puede generar warnings).
 *
 * Ejemplo: const { data, loading, error, refetch } = useApi(() => endpoints.artists.top());
 */

import { useState, useEffect, useCallback } from "react";
import { ApiError } from "@/lib/api";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useApi<T>(fetcher: () => Promise<T>): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(() => {
    setLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        setData(result);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Error desconocido");
        }
        setLoading(false);
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}
