/**
 * AppLayout — wraps all protected pages with Navbar + main content area.
 * Design: Glassmorphism Premium Dark
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
