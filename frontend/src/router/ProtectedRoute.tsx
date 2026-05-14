/**
 * ProtectedRoute — wraps any route that requires authentication.
 * If the JWT token is missing or expired, redirects to /login.
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
