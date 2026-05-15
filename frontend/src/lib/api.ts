/**
 * api.ts — Cliente HTTP tipado para el backend FastAPI.
 *
 * - Inyecta automáticamente el Bearer token desde localStorage ("app_token").
 * - Un 401 llama a logout() y lanza ApiError (redirige a /login).
 * - Expone `api.get/post/put/delete` genéricos y `endpoints` con métodos nombrados.
 * - Base URL: variable de entorno VITE_API_URL (fallback: http://127.0.0.1:8000).
 *
 * Nota: PeakHourCard.tsx y EtlHistoryTable.tsx usan fetch directo en lugar de este módulo.
 */

import { getToken, logout } from "./auth";

// Usar 127.0.0.1 explícitamente para que coincida con el CORS del backend
const BASE_URL = (import.meta.env.VITE_API_URL as string) || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string | number | boolean>;
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, params, headers: extraHeaders, ...rest } = options;

  // Build URL with optional query params
  const url = new URL(`${BASE_URL}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }

  // Inject auth token
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(extraHeaders as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url.toString(), {
    ...rest,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Handle 401 → logout and redirect
  if (response.status === 401) {
    logout();
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }
    const message =
      typeof errorData === "object" && errorData !== null && "detail" in errorData
        ? String((errorData as { detail: string }).detail)
        : `HTTP ${response.status}`;
    throw new ApiError(response.status, message, errorData);
  }

  // Handle empty responses (e.g. 204 No Content)
  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

// ─── Typed API methods ────────────────────────────────────────────────────────

export const api = {
  get: <T>(path: string, params?: Record<string, string | number | boolean>) =>
    request<T>(path, { method: "GET", params }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body }),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body }),

  delete: <T>(path: string) =>
    request<T>(path, { method: "DELETE" }),
};

// ─── Endpoint helpers ─────────────────────────────────────────────────────────

import type { UserProfile } from "@/types/user";
import type { TopArtistsResponse } from "@/types/artist";
import type { TopTracksResponse } from "@/types/track";
import type { PeakHour, GenresResponse, QuickStats } from "@/types/history";
import type { EtlStatusResponse, EtlRunResponse } from "@/types/etl";

export const endpoints = {
  profile: {
    me: () => api.get<UserProfile>("/v1/profile/me"),
  },
  artists: {
    top: () => api.get<TopArtistsResponse>("/v1/artists/top"),
  },
  tracks: {
    top: () => api.get<TopTracksResponse>("/v1/tracks/top"),
  },
  history: {
    peakHour: () => api.get<PeakHour>("/v1/history/peak-hour"),
    genres: () => api.get<GenresResponse>("/v1/history/genres"),
    quickStats: () => api.get<QuickStats>("/v1/history/stats"),
  },
  etl: {
    status: () => api.get<EtlStatusResponse>("/v1/etl/status"),
    run: () => api.post<EtlRunResponse>("/v1/etl/run"),
  },
};