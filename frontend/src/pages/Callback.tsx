/**
 * Callback.tsx — Página de callback OAuth post-autenticación.
 *
 * El backend redirige aquí con un código de un solo uso: `/callback?code=<codigo>`.
 *
 * Flujo al montar el componente:
 * 1. Lee `?code` y limpia la URL con `history.replaceState`.
 * 2. Lo cambia por el JWT con POST /v1/auth/exchange (el JWT nunca va en la URL).
 * 3. Guarda el JWT en localStorage["app_token"] y va a /dashboard.
 *
 * Sin código, o si el intercambio falla, vuelve a /login.
 *
 * Diseño: pantalla de carga con logo animado y spinner. Fondo #121212.
 */

import { useEffect, useRef } from "react";
import { useLocation } from "wouter";
import { saveToken } from "@/lib/auth";
import { endpoints } from "@/lib/api";
import { Music2 } from "lucide-react";

export default function Callback() {
  const [, setLocation] = useLocation();

  // El código solo sirve una vez: evita un segundo intercambio si el efecto se repite.
  const exchanged = useRef(false);

  useEffect(() => {
    if (exchanged.current) return;
    exchanged.current = true;

    const code = new URLSearchParams(window.location.search).get("code");
    window.history.replaceState({}, document.title, window.location.pathname);

    if (!code) {
      setLocation("/login");
      return;
    }

    endpoints.auth
      .exchange(code)
      .then(({ token }) => {
        saveToken(token);
        setLocation("/dashboard");
      })
      .catch(() => setLocation("/login"));
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
