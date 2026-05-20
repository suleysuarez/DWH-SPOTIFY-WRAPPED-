import { lazy, Suspense, useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch, Redirect, useLocation } from "wouter";
import { AnimatePresence, motion } from "framer-motion";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import ProtectedRoute from "./router/ProtectedRoute";
import SplashScreen from "./components/SplashScreen";
import { SkeletonCard } from "./components/ui/SkeletonCard";

// Lazy-loaded pages — each page is a separate JS chunk loaded on demand
const Login = lazy(() => import("./pages/Login"));
const Callback = lazy(() => import("./pages/Callback"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Profile = lazy(() => import("./pages/Profile"));
const Etl = lazy(() => import("./pages/Etl"));
const NotFound = lazy(() => import("./pages/NotFound"));

const pageVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2, ease: "easeIn" } },
};

function PageLoader() {
  return (
    <div className="p-6 space-y-4">
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}

function Router() {
  const [location] = useLocation();

  return (
    // AnimatePresence needs motion.div as a direct child with key={location}
    // so it can track exit → enter transitions on route change.
    <AnimatePresence mode="wait">
      <motion.div
        key={location}
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        style={{ width: "100%" }}
      >
        <Suspense fallback={<PageLoader />}>
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

            {/* Root redirect to dashboard */}
            <Route path="/">
              <Redirect to="/dashboard" />
            </Route>

            {/* 404 fallback */}
            <Route component={NotFound} />
          </Switch>
        </Suspense>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  const [splashDone, setSplashDone] = useState(false);

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
          {!splashDone && <SplashScreen onComplete={() => setSplashDone(true)} />}
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
