/**
 * const.ts — Re-exportaciones y constantes del frontend (legado Manus).
 *
 * Re-exporta COOKIE_NAME y ONE_YEAR_MS de shared/const.ts — constantes del portal Manus
 * que no se usan en el flujo OAuth activo (el auth usa JWT en localStorage["app_token"]).
 *
 * getLoginUrl() construye la URL de un portal OAuth genérico (VITE_OAUTH_PORTAL_URL).
 * ⚠️  Esta función NO se usa en el flujo activo. El login real redirige al backend
 * FastAPI en /v1/auth/login, sin pasar por esta función.
 */

export { COOKIE_NAME, ONE_YEAR_MS } from "@shared/const";

// Generate login URL at runtime so redirect URI reflects the current origin.
export const getLoginUrl = () => {
  const oauthPortalUrl = import.meta.env.VITE_OAUTH_PORTAL_URL;
  const appId = import.meta.env.VITE_APP_ID;
  const redirectUri = `${window.location.origin}/api/oauth/callback`;
  const state = btoa(redirectUri);

  const url = new URL(`${oauthPortalUrl}/app-auth`);
  url.searchParams.set("appId", appId);
  url.searchParams.set("redirectUri", redirectUri);
  url.searchParams.set("state", state);
  url.searchParams.set("type", "signIn");

  return url.toString();
};
