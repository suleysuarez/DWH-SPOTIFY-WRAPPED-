/**
 * ProtectedRoute — Guarda de autenticación para rutas privadas.
 *
 * Llama a isTokenValid() de lib/auth.ts: verifica que el JWT esté presente en
 * localStorage ("app_token") y que el claim `exp` no haya vencido.
 * Si el token es inválido o ha expirado, redirige a /login con Wouter <Redirect>.
 * La validación es síncrona (lectura de localStorage) — no muestra spinner de carga.
 */

import { isTokenValid } from "@/lib/auth";
import { Redirect } from "wouter";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  if (!isTokenValid()) {
    return <Redirect to="/login" />;
  }
  return <>{children}</>;
}
