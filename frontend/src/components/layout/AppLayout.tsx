/**
 * AppLayout — Shell de navegación para todas las rutas protegidas.
 *
 * Composición: Navbar sticky + <main> con container centrado.
 * Fondo: #121212 (Glassmorphism Premium Dark).
 * Todas las páginas protegidas (/dashboard, /profile, /etl) se renderizan como `children`.
 */

import Navbar from "./Navbar";

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen" style={{ background: "#121212" }}>
      <Navbar />
      <main className="container py-8">{children}</main>
    </div>
  );
}
