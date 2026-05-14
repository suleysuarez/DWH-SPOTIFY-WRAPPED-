/**
 * App.tsx — Root component with routing.
 * Routes:
 *   /login     → Login (public)
 *   /callback  → Callback (public, processes JWT)
 *   /dashboard → Dashboard (protected)
 *   /profile   → Profile (protected)
 *   /etl       → ETL (protected)
 *
 * Design: Glassmorphism Premium Dark (Spotify-inspired)
 * Theme: dark by default — matches #121212 background
 */

import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch, Redirect } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import ProtectedRoute from "./router/ProtectedRoute";

// Pages
import Login from "./pages/Login";
import Callback from "./pages/Callback";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import Etl from "./pages/Etl";
import NotFound from "./pages/NotFound";

function Router() {
  return (
    <Switch>
      {/* Public routes */}
      <Route path="/login" component={Login} />
      <Route path="/callback" component={Callback} />

      {/* Protected routes */}
      <Route path="/dashboard">
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      </Route>

      <Route path="/profile">
        <ProtectedRoute>
          <Profile />
        </ProtectedRoute>
      </Route>

      <Route path="/etl">
        <ProtectedRoute>
          <Etl />
        </ProtectedRoute>
      </Route>

      {/* Root redirect to dashboard (ProtectedRoute handles auth check) */}
      <Route path="/">
        <Redirect to="/dashboard" />
      </Route>

      {/* 404 fallback */}
      <Route component={NotFound} />
    </Switch>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          <Toaster
            theme="dark"
            toastOptions={{
              style: {
                background: "rgba(24,24,24,0.95)",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "#fff",
              },
            }}
          />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
