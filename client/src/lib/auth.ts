/**
 * Authentication helpers for JWT token management.
 * The token is stored in localStorage under the key "app_token".
 * The frontend NEVER talks directly to Spotify API — all auth
 * is handled by the FastAPI backend via OAuth PKCE.
 */

const TOKEN_KEY = "app_token";

/** Save the JWT token to localStorage */
export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/** Retrieve the JWT token from localStorage */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/** Remove the JWT token (logout) */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Decode the JWT payload (base64url) without verifying the signature.
 * Signature verification is the backend's responsibility.
 */
function decodePayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1];
    // Base64url → base64 → JSON
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(base64);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

/**
 * Check whether the stored token is present and not expired.
 * Returns true if the token is valid, false otherwise.
 */
export function isTokenValid(): boolean {
  const token = getToken();
  if (!token) return false;

  const payload = decodePayload(token);
  if (!payload) return false;

  const exp = payload["exp"];
  if (typeof exp !== "number") return true; // No expiry claim → treat as valid

  const nowSeconds = Math.floor(Date.now() / 1000);
  return exp > nowSeconds;
}

/** Logout: remove token and redirect to /login */
export function logout(): void {
  removeToken();
  window.location.href = "/login";
}
