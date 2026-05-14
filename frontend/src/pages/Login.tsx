/**
 * Login Page
 * Design: Glassmorphism Premium Dark
 * - Fullscreen centered layout
 * - Large Spotify-inspired card with backdrop-blur
 * - Animated floating decorative elements
 * - Single CTA: "Conectar con Spotify"
 */

import { Music2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

const BACKEND_LOGIN_URL = "http://127.0.0.1:8000/v1/auth/login";

export default function Login() {
  const handleConnect = async () => {
    const res = await fetch(BACKEND_LOGIN_URL);
    const data = await res.json();
    window.location.href = data.authorization_url;
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: "#121212" }}
    >
      {/* Ambient background blobs */}
      <div
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(29,185,84,0.12) 0%, transparent 70%)",
          filter: "blur(40px)",
          animation: "float1 8s ease-in-out infinite",
        }}
      />
      <div
        className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(29,185,84,0.08) 0%, transparent 70%)",
          filter: "blur(60px)",
          animation: "float2 10s ease-in-out infinite",
        }}
      />
      <div
        className="absolute top-1/2 right-1/3 w-64 h-64 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(100,100,255,0.06) 0%, transparent 70%)",
          filter: "blur(50px)",
          animation: "float3 12s ease-in-out infinite",
        }}
      />

      {/* Floating decorative dots */}
      {[...Array(6)].map((_, i) => (
        <div
          key={i}
          className="absolute rounded-full pointer-events-none"
          style={{
            width: `${4 + (i % 3) * 2}px`,
            height: `${4 + (i % 3) * 2}px`,
            background: "rgba(29, 185, 84, 0.3)",
            top: `${15 + i * 12}%`,
            left: `${8 + i * 14}%`,
            animation: `floatDot${i % 3} ${5 + i}s ease-in-out infinite`,
            animationDelay: `${i * 0.8}s`,
          }}
        />
      ))}

      {/* Main card */}
      <div
        className="relative z-10 w-full max-w-md mx-4 rounded-2xl p-10 flex flex-col items-center text-center"
        style={{
          background: "rgba(24, 24, 24, 0.85)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow: "0 32px 80px rgba(0,0,0,0.5), 0 0 60px rgba(29,185,84,0.08)",
        }}
      >
        {/* Logo */}
        <div
          className="w-20 h-20 rounded-full flex items-center justify-center mb-6"
          style={{
            background: "linear-gradient(135deg, #1DB954 0%, #1ed760 100%)",
            boxShadow: "0 8px 32px rgba(29,185,84,0.4)",
          }}
        >
          <Music2 className="w-9 h-9 text-black" strokeWidth={2.5} />
        </div>

        {/* Title */}
        <h1
          className="text-3xl font-black text-white mb-1 tracking-tight"
          style={{ fontFamily: "Nunito, sans-serif" }}
        >
          Mi Spotify Wrapped
        </h1>
        <p className="text-sm font-medium mb-2" style={{ color: "#1DB954" }}>
          Personal Data Warehouse
        </p>
        <p className="text-sm text-white/40 mb-8 leading-relaxed">
          Conecta tu cuenta de Spotify para explorar tu historial musical y analíticas personales.
        </p>

        {/* CTA Button */}
        <Button
          onClick={handleConnect}
          className="w-full h-12 text-base font-bold rounded-full gap-3 transition-all duration-200 active:scale-95"
          style={{
            background: "linear-gradient(135deg, #1DB954, #1ed760)",
            color: "#000",
            boxShadow: "0 4px 24px rgba(29,185,84,0.35)",
            fontFamily: "Nunito, sans-serif",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 8px 32px rgba(29,185,84,0.5)";
            (e.currentTarget as HTMLButtonElement).style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 4px 24px rgba(29,185,84,0.35)";
            (e.currentTarget as HTMLButtonElement).style.transform = "translateY(0)";
          }}
        >
          <Sparkles className="w-4 h-4" />
          Conectar con Spotify
        </Button>

        <p className="text-xs text-white/25 mt-6">
          Al conectar, autorizas el acceso de lectura a tu historial de Spotify.
        </p>
      </div>

      {/* Animation keyframes */}
      <style>{`
        @keyframes float1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(20px, -30px) scale(1.05); }
        }
        @keyframes float2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-25px, 20px) scale(0.95); }
        }
        @keyframes float3 {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(15px, 25px); }
        }
        @keyframes floatDot0 {
          0%, 100% { transform: translateY(0); opacity: 0.3; }
          50% { transform: translateY(-12px); opacity: 0.8; }
        }
        @keyframes floatDot1 {
          0%, 100% { transform: translateY(0); opacity: 0.2; }
          50% { transform: translateY(-18px); opacity: 0.6; }
        }
        @keyframes floatDot2 {
          0%, 100% { transform: translateY(0); opacity: 0.4; }
          50% { transform: translateY(-8px); opacity: 0.9; }
        }
      `}</style>
    </div>
  );
}