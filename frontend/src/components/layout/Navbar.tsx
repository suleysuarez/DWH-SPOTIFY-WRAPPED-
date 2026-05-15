/**
 * Navbar — Barra de navegación sticky para rutas protegidas.
 *
 * Diseño: glassmorphism (rgba(18,18,18,0.85) + backdrop-blur(16px)).
 * Rutas: /dashboard, /profile, /etl con indicador verde activo (#1DB954).
 * El botón de logout llama a logout() de lib/auth.ts (borra "app_token" y redirige a /login).
 * La ruta activa se detecta con useLocation() de Wouter.
 */

import { logout } from "@/lib/auth";
import { LayoutDashboard, User, Database, LogOut } from "lucide-react";
import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const navLinks = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/profile", label: "Perfil", icon: User },
  { href: "/etl", label: "ETL", icon: Database },
];

export default function Navbar() {
  const [location] = useLocation();

  const handleLogout = () => {
    logout();
  };

  return (
    <header
      className="sticky top-0 z-50 w-full"
      style={{
        background: "rgba(18, 18, 18, 0.85)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <div className="container flex items-center justify-between h-16">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <img
            src="/images/logo_spotify.png"
            alt="Spotify"
            className="w-8 h-8 object-contain transition-all duration-200 group-hover:scale-110"
          />
          <span
            className="font-bold text-sm hidden sm:block"
            style={{ fontFamily: "DM Sans, sans-serif", color: "#fff" }}
          >
            Spotify <span style={{ color: "#1DB954" }}>Wrapped</span>
          </span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          {navLinks.map(({ href, label, icon: Icon }) => {
            const isActive = location === href || location.startsWith(href + "/");
            return (
              <Link key={href} href={href}>
                <button
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                    isActive
                      ? "text-white"
                      : "text-white/50 hover:text-white/80 hover:bg-white/5"
                  )}
                  style={
                    isActive
                      ? {
                          background: "rgba(29, 185, 84, 0.12)",
                          color: "#1DB954",
                        }
                      : {}
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:block">{label}</span>
                </button>
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-white/40 hover:text-red-400 hover:bg-red-400/10 transition-all duration-200"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Cerrar sesión</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </header>
  );
}
