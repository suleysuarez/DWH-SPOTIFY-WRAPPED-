/**
 * Callback.tsx — Página de callback OAuth post-autenticación.
 *
 * Recibe el JWT que el backend agrega como query param tras el OAuth de Spotify:
 *   `/callback?token=<jwt>`
 *
 * Flujo al montar el componente:
 * 1. Lee `?token` de la URL con URLSearchParams.
 * 2. Llama a `saveToken(token)` → guarda en localStorage["app_token"].
 * 3. Limpia la URL con `history.replaceState` para eliminar el token del historial.
 * 4. Tras 800ms redirige a /dashboard (ProtectedRoute validará el token).
 *
 * Si no hay token en la URL, igual redirige a /dashboard y ProtectedRoute
 * enviará al usuario a /login.
 *
 * Diseño: pantalla de carga con logo animado y spinner. Fondo #121212.
 */

import { useEffect } from "react";
import { useLocation } from "wouter";
import { saveToken } from "@/lib/auth";
import { Music2 } from "lucide-react";

export default function Callback() {
  const [, setLocation] = useLocation();

  useEffect(() => {
    // Extract token from URL search params
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (token) {
      // Save to localStorage
      saveToken(token);
      // Clean URL (remove query params from browser history)
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    // Redirect to dashboard (with or without token — ProtectedRoute handles missing token)
    const timer = setTimeout(() => {
      setLocation("/dashboard");
    }, 800);

    return () => clearTimeout(timer);
  }, [setLocation]);

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-6"
      style={{ background: "#121212" }}
    >
      {/* Animated logo */}
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center"
        style={{
          background: "linear-gradient(135deg, #1DB954, #1ed760)",
          boxShadow: "0 0 40px rgba(29,185,84,0.4)",
          animation: "pulse 1.5s ease-in-out infinite",
        }}
      >
        <Music2 className="w-7 h-7 text-black" strokeWidth={2.5} />
      </div>

      {/* Spinner */}
      <div className="flex items-center gap-3">
        <div
          className="w-5 h-5 rounded-full border-2 border-t-transparent"
          style={{
            borderColor: "rgba(29,185,84,0.3)",
            borderTopColor: "#1DB954",
            animation: "spin 0.8s linear infinite",
          }}
        />
        <p className="text-white/70 text-sm font-medium">
          Autenticando con Spotify...
        </p>
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 40px rgba(29,185,84,0.4); }
          50% { box-shadow: 0 0 60px rgba(29,185,84,0.7); }
        }
      `}</style>
    </div>
  );
}
