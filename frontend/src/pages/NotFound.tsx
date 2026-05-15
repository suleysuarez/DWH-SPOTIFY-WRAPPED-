/**
 * NotFound.tsx — Página 404.
 *
 * Se muestra para cualquier ruta no definida en el Switch de App.tsx.
 * Botón "Volver al inicio" redirige a "/" (que a su vez hace redirect a /dashboard).
 */
import { Button } from "@/components/ui/button";
import { AlertCircle, Home } from "lucide-react";
import { useLocation } from "wouter";

export default function NotFound() {
  const [, setLocation] = useLocation();

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center"
      style={{ background: "#121212" }}
    >
      <div className="flex flex-col items-center text-center px-6">
        <div
          className="w-20 h-20 rounded-full flex items-center justify-center mb-6"
          style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)" }}
        >
          <AlertCircle className="w-9 h-9 text-red-400" />
        </div>
        <h1
          className="text-6xl font-black text-white mb-2"
          style={{ fontFamily: "DM Sans, sans-serif" }}
        >
          404
        </h1>
        <p className="text-white/40 mb-8">La página que buscas no existe.</p>
        <Button
          onClick={() => setLocation("/")}
          className="gap-2 font-bold"
          style={{ background: "#1DB954", color: "#000" }}
        >
          <Home className="w-4 h-4" />
          Volver al inicio
        </Button>
      </div>
    </div>
  );
}
